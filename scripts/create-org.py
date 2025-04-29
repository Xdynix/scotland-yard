import asyncio
import os
from datetime import datetime
from typing import Annotated

import typer
from faker import Faker, generator
from loguru import logger
from tortoise.transactions import atomic

from app.models import Item, Organization, SharingLink, User
from app.random import (
    allocate_by_dirichlet,
    generate_poisson_tree,
    sample_lambdas_by_node_count,
)
from app.utils import with_tortoise

FAKER_LOCALES = [
    "en_US",
    "es_ES",
    "fr_FR",
    "it_IT",
    "ja_JP",
    "zh_CN",
]

# Dirichlet distribution concentration parameters:
# -----------------------------------------------
# These α (alpha) values shape how “peaked” or “flat” the random allocations are.
#  - α < 1: Produces sparse, highly skewed draws (most mass on few categories).
#  - α = 1: Uniform distribution over categories.
#  - α > 1: More even, balanced allocations across categories.
ITEM_ALPHA = 0.7
SHARING_LINK_ALPHA = 0.3

BULK_BATCH_SIZE = 1000


@logger.catch
@with_tortoise
@atomic()
async def run(
    name: str,
    user_count: int,
    items_count: int,
    sharing_link_count: int,
    seed: int | None,
) -> None:
    if seed is None:
        seed = int.from_bytes(os.urandom(8))
    Faker.seed(seed)
    logger.info(f"Creating new organization. Seed: {seed}")

    fake = Faker(locale=FAKER_LOCALES)

    org = await Organization.create(name=name)
    logger.info(f"Organization created, id: {org.id}.")

    logger.info("Creating users.")
    await User.bulk_create(
        [
            User(
                organization=org,
                username=f"{i}-{fake.user_name()}",
                email=f"{i}-{fake.email()}",
                active=fake.boolean(chance_of_getting_true=80),
                role=fake.random_element(User.Role),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            for i in range(user_count)
        ],
        batch_size=BULK_BATCH_SIZE,
    )
    logger.info(f"{user_count} users created.")

    logger.info("Creating items.")
    user_ids = await org.users.order_by("id").values_list("id", flat=True)
    items_per_user = allocate_by_dirichlet(
        generator.random,
        categories=user_count,
        total=items_count,
        concentration=ITEM_ALPHA,
    )
    item_tree_rates = sample_lambdas_by_node_count(generator.random, items_per_user)
    for user_id, user_items_count, item_tree_rate in zip(
        user_ids,
        items_per_user,
        item_tree_rates,
        strict=True,
    ):
        tree = generate_poisson_tree(
            generator.random,
            user_items_count,
            rate=item_tree_rate,
        )
        parent_lookup: dict[int, int] = {}
        node_to_item_id: dict[int, int] = {}
        for node, children in sorted(tree.items()):
            for child in children:
                parent_lookup[child] = node
            parent = parent_lookup.get(node, -1)

            is_file = not children
            item = await Item.create(
                owner_id=user_id,
                parent_id=node_to_item_id.get(parent),
                name=f"{node}-{fake.file_name() if is_file else fake.slug()}",
                type=Item.Type.FILE if is_file else Item.Type.FOLDER,
                file_size=fake.random_int(max=2**30) if is_file else 0,
            )

            node_to_item_id[node] = item.id
            del item

        logger.info(f"{user_items_count} items created for user {user_id}.")

    logger.info("Creating sharing links.")
    item_ids = (
        await Item.filter(owner__organization_id=org.id)
        .order_by("id")
        .values_list("id", flat=True)
    )
    sharing_links_per_item = allocate_by_dirichlet(
        generator.random,
        categories=items_count,
        total=sharing_link_count,
        concentration=SHARING_LINK_ALPHA,
    )
    for item_id, item_sharing_link_count in zip(
        item_ids,
        sharing_links_per_item,
        strict=True,
    ):
        if not item_sharing_link_count:
            continue
        await SharingLink.bulk_create(
            [
                SharingLink(
                    item_id=item_id,
                    token=fake.uuid4(),
                    permission=fake.random_element(SharingLink.Permission),
                    expire_time=(
                        fake.date_time(end_datetime=datetime(2099, 1, 1))
                        if fake.boolean()
                        else None
                    ),
                )
                for _ in range(item_sharing_link_count)
            ],
            batch_size=BULK_BATCH_SIZE,
        )
        logger.info(
            f"{item_sharing_link_count} sharing links created for item {item_id}."
        )


def main(
    name: Annotated[
        str,
        typer.Option(help="Name of organization."),
    ],
    user_count: Annotated[
        int,
        typer.Option(help="Number of users to create."),
    ] = 100,
    item_count: Annotated[
        int,
        typer.Option(help="Number of items to create."),
    ] = 10_000,
    sharing_link_count: Annotated[
        int,
        typer.Option(
            help="Number of sharing links to create.",
        ),
    ] = 100_000,
    seed: Annotated[
        int | None,
        typer.Option(help="Specify the seed for RNG."),
    ] = None,
) -> None:
    asyncio.run(
        run(
            name=name,
            user_count=user_count,
            items_count=item_count,
            sharing_link_count=sharing_link_count,
            seed=seed,
        )
    )


if __name__ == "__main__":
    typer.run(main)
