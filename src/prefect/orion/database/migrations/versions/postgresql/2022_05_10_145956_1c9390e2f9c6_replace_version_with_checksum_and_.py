"""Replace version with checksum and create block_type table

Revision ID: 1c9390e2f9c6
Revises: d38c5e6a9115
Create Date: 2022-05-10 14:59:56.299921

"""

import sqlalchemy as sa
from alembic import op

import prefect
from prefect.blocks.core import Block

# revision identifiers, used by Alembic.
revision = "1c9390e2f9c6"
down_revision = "d38c5e6a9115"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "block_type",
        sa.Column(
            "id",
            prefect.orion.utilities.database.UUID(),
            server_default=sa.text("(GEN_RANDOM_UUID())"),
            nullable=False,
        ),
        sa.Column(
            "created",
            prefect.orion.utilities.database.Timestamp(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated",
            prefect.orion.utilities.database.Timestamp(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("logo_url", sa.String(), nullable=True),
        sa.Column("documentation_url", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_block_type")),
    )
    op.create_index(
        op.f("ix_block_type__updated"), "block_type", ["updated"], unique=False
    )
    op.create_index("uq_block_type__name", "block_type", ["name"], unique=True)
    op.add_column(
        "block_document",
        sa.Column(
            "block_type_id", prefect.orion.utilities.database.UUID(), nullable=True
        ),
    )
    op.drop_index("uq_block__schema_id_name", table_name="block_document")
    op.create_index(
        "uq_block__type_id_name",
        "block_document",
        ["block_type_id", "name"],
        unique=True,
    )
    op.create_foreign_key(
        op.f("fk_block_document__block_type_id__block_type"),
        "block_document",
        "block_type",
        ["block_type_id"],
        ["id"],
        ondelete="cascade",
    )
    op.add_column("block_schema", sa.Column("checksum", sa.String(), nullable=True))
    op.add_column(
        "block_schema",
        sa.Column(
            "block_type_id", prefect.orion.utilities.database.UUID(), nullable=True
        ),
    )
    op.drop_index("uq_block_schema__name_version", table_name="block_schema")
    op.create_index(
        op.f("ix_block_schema__checksum"), "block_schema", ["checksum"], unique=False
    )
    op.create_index(
        "uq_block_schema__checksum", "block_schema", ["checksum"], unique=True
    )
    op.create_foreign_key(
        op.f("fk_block_schema__block_type_id__block_type"),
        "block_schema",
        "block_type",
        ["block_type_id"],
        ["id"],
        ondelete="cascade",
    )
    op.drop_column("block_schema", "version")

    # Add checksums and block types for existing block schemas
    connection = op.get_bind()
    meta_data = sa.MetaData(bind=connection)
    meta_data.reflect()
    BLOCK_SCHEMA = meta_data.tables["block_schema"]
    BLOCK_TYPE = meta_data.tables["block_type"]
    BLOCK_DOCUMENT = meta_data.tables["block_document"]
    results = connection.execute(
        sa.select([BLOCK_SCHEMA.c.id, BLOCK_SCHEMA.c.name, BLOCK_SCHEMA.c.fields])
    )
    for id, name, fields in results:
        schema_checksum = Block._calculate_schema_checksum(fields)
        # Add checksum
        connection.execute(
            sa.update(BLOCK_SCHEMA)
            .where(BLOCK_SCHEMA.c.id == id)
            .values(checksum=schema_checksum)
        )
        # Create corresponding block type
        block_type_result = connection.execute(
            sa.select([BLOCK_TYPE.c.id]).where(BLOCK_TYPE.c.name == name)
        ).first()
        if block_type_result is None:
            connection.execute(sa.insert(BLOCK_TYPE).values(name=name))
        block_type_result = connection.execute(
            sa.select([BLOCK_TYPE.c.id]).where(BLOCK_TYPE.c.name == name)
        ).first()
        new_block_type_id = block_type_result[0]
        connection.execute(
            sa.update(BLOCK_SCHEMA)
            .where(BLOCK_SCHEMA.c.id == id)
            .values(block_type_id=new_block_type_id)
        )
        # Associate new block type will all block documents for this block schema
        block_document_results = connection.execute(
            sa.select([BLOCK_DOCUMENT.c.id]).where(
                BLOCK_DOCUMENT.c.block_schema_id == id
            )
        ).all()
        for block_document in block_document_results:
            connection.execute(
                sa.update(BLOCK_DOCUMENT)
                .where(BLOCK_DOCUMENT.c.id == block_document[0])
                .values(block_type_id=new_block_type_id)
            )

    op.drop_column("block_schema", "name")
    op.alter_column(
        "block_schema", "checksum", existing_type=sa.VARCHAR(), nullable=False
    )
    op.alter_column(
        "block_schema", "block_type_id", existing_type=sa.VARCHAR(), nullable=False
    )
    op.alter_column(
        "block_document", "block_type_id", existing_type=sa.VARCHAR(), nullable=False
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "block_schema",
        sa.Column("version", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "block_schema",
        sa.Column("name", sa.VARCHAR(), autoincrement=False, nullable=True),
    )
    op.drop_constraint(
        op.f("fk_block_schema__block_type_id__block_type"),
        "block_schema",
        type_="foreignkey",
    )
    op.drop_index("uq_block_schema__checksum", table_name="block_schema")
    op.drop_index(op.f("ix_block_schema__checksum"), table_name="block_schema")
    op.create_index(
        "uq_block_schema__name_version",
        "block_schema",
        ["name", "version"],
        unique=False,
    )
    op.drop_column("block_schema", "block_type_id")
    op.drop_column("block_schema", "checksum")
    op.drop_constraint(
        op.f("fk_block_document__block_type_id__block_type"),
        "block_document",
        type_="foreignkey",
    )
    op.drop_index("uq_block__type_id_name", table_name="block_document")
    op.create_index(
        "uq_block__schema_id_name",
        "block_document",
        ["block_schema_id", "name"],
        unique=False,
    )
    op.drop_column("block_document", "block_type_id")
    op.drop_index("uq_block_type__name", table_name="block_type")
    op.drop_index(op.f("ix_block_type__updated"), table_name="block_type")
    op.drop_table("block_type")
    # ### end Alembic commands ###
