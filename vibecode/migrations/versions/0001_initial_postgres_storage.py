"""Initial PostgreSQL storage

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[Sequence[str], None] = None
depends_on: Union[Sequence[str], None] = None


def upgrade() -> None:
    # Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            unique=True,
        ),
        sa.Column("username", sa.String(100), nullable=False, unique=True),
        sa.Column("email", sa.String(255), unique=True),
        sa.Column("display_name", sa.String(255)),
        sa.Column(
            "settings",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    # projects
    op.create_table(
        "projects",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            unique=True,
        ),
        sa.Column(
            "owner_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("root_path", sa.Text()),
        sa.Column("description", sa.Text()),
        sa.Column("project_hash", sa.String(64)),
        sa.Column(
            "settings",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("idx_projects_owner", "projects", ["owner_id"])
    op.create_index("idx_projects_project_id", "projects", ["project_id"])
    op.create_index("idx_projects_project_hash", "projects", ["project_hash"])

    # success_patterns
    op.create_table(
        "success_patterns",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "pattern_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            unique=True,
        ),
        sa.Column(
            "project_id",
            sa.BigInteger(),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "creator_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("intent_description", sa.Text(), nullable=False),
        sa.Column("language", sa.String(50)),
        sa.Column("framework", sa.String(100)),
        sa.Column("file_type", sa.String(100)),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "affected_files",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("original_prompt", sa.Text()),
        sa.Column("reasoning_summary", sa.Text()),
        sa.Column(
            "reasoning_steps",
            postgresql.JSONB,
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column("code_before", sa.Text()),
        sa.Column("code_after", sa.Text()),
        sa.Column("diff", sa.Text()),
        sa.Column("explanation", sa.Text()),
        sa.Column("token_cost_original", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("token_cost_retrieval", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("estimated_tokens_saved", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("confidence_score", sa.REAL(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("success_rate", sa.REAL(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("source_type", sa.String(50)),
        sa.Column("source_ref", sa.Text()),
        sa.Column("source_commit", sa.String(64)),
        sa.Column("source_file_path", sa.Text()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("last_used", sa.TIMESTAMP(timezone=True)),
        sa.CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="valid_success_confidence"),
        sa.CheckConstraint("success_rate >= 0 AND success_rate <= 1", name="valid_success_rate"),
        sa.CheckConstraint(
            "token_cost_original >= 0 AND token_cost_retrieval >= 0 AND estimated_tokens_saved >= 0",
            name="valid_success_tokens",
        ),
    )
    op.create_index("idx_success_patterns_project", "success_patterns", ["project_id"])
    op.create_index("idx_success_patterns_creator", "success_patterns", ["creator_id"])
    op.create_index("idx_success_patterns_language", "success_patterns", ["language"])
    op.create_index("idx_success_patterns_framework", "success_patterns", ["framework"])
    op.create_index("idx_success_patterns_tags", "success_patterns", ["tags"], postgresql_using="gin")
    op.create_index("idx_success_patterns_active", "success_patterns", ["is_active"], postgresql_where=sa.text("is_active = true"))
    op.create_index("idx_success_patterns_last_used", "success_patterns", [sa.text("last_used DESC NULLS LAST")])
    op.create_index(
        "idx_success_patterns_project_content_hash",
        "success_patterns",
        ["project_id", "content_hash"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false AND content_hash IS NOT NULL"),
    )
    op.execute(
        """
        CREATE INDEX idx_success_patterns_fts ON success_patterns
        USING GIN(
            to_tsvector(
                'english',
                coalesce(name, '') || ' ' ||
                coalesce(intent_description, '') || ' ' ||
                coalesce(reasoning_summary, '') || ' ' ||
                coalesce(explanation, '')
            )
        );
        """
    )

    # failure_patterns
    op.create_table(
        "failure_patterns",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "failure_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            unique=True,
        ),
        sa.Column(
            "project_id",
            sa.BigInteger(),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "creator_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("task_intent", sa.Text(), nullable=False),
        sa.Column("bad_suggestion", sa.Text(), nullable=False),
        sa.Column("failure_reason", sa.Text(), nullable=False),
        sa.Column("corrected_approach", sa.Text()),
        sa.Column("prevention_rule", sa.Text(), nullable=False),
        sa.Column("language", sa.String(50)),
        sa.Column("framework", sa.String(100)),
        sa.Column(
            "affected_files",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("severity", sa.String(20), nullable=False, server_default=sa.text("'medium'"))
        ,
        sa.Column("confidence_score", sa.REAL(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("usage_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("source_type", sa.String(50)),
        sa.Column("source_ref", sa.Text()),
        sa.Column("source_commit", sa.String(64)),
        sa.Column("source_file_path", sa.Text()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("last_used", sa.TIMESTAMP(timezone=True)),
        sa.CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="valid_failure_confidence"),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="valid_failure_severity",
        ),
    )
    op.create_index("idx_failure_patterns_project", "failure_patterns", ["project_id"])
    op.create_index("idx_failure_patterns_creator", "failure_patterns", ["creator_id"])
    op.create_index("idx_failure_patterns_language", "failure_patterns", ["language"])
    op.create_index("idx_failure_patterns_framework", "failure_patterns", ["framework"])
    op.create_index("idx_failure_patterns_tags", "failure_patterns", ["tags"], postgresql_using="gin")
    op.create_index("idx_failure_patterns_severity", "failure_patterns", ["severity"])
    op.create_index("idx_failure_patterns_active", "failure_patterns", ["is_active"], postgresql_where=sa.text("is_active = true"))
    op.create_index(
        "idx_failure_patterns_project_content_hash",
        "failure_patterns",
        ["project_id", "content_hash"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false AND content_hash IS NOT NULL"),
    )
    op.execute(
        """
        CREATE INDEX idx_failure_patterns_fts ON failure_patterns
        USING GIN(
            to_tsvector(
                'english',
                coalesce(task_intent, '') || ' ' ||
                coalesce(bad_suggestion, '') || ' ' ||
                coalesce(failure_reason, '') || ' ' ||
                coalesce(corrected_approach, '') || ' ' ||
                coalesce(prevention_rule, '')
            )
        );
        """
    )

    # project_rules
    op.create_table(
        "project_rules",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "rule_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            unique=True,
        ),
        sa.Column(
            "project_id",
            sa.BigInteger(),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
        ),
        sa.Column(
            "creator_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("rule_text", sa.Text(), nullable=False),
        sa.Column("rule_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False, server_default=sa.text("'medium'")),
        sa.Column(
            "source_success_pattern_id",
            sa.BigInteger(),
            sa.ForeignKey("success_patterns.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "source_failure_id",
            sa.BigInteger(),
            sa.ForeignKey("failure_patterns.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "tags",
            postgresql.ARRAY(sa.String()),
            nullable=False,
            server_default=sa.text("ARRAY[]::text[]"),
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="valid_rule_severity",
        ),
    )
    op.create_index("idx_project_rules_project", "project_rules", ["project_id"])
    op.create_index("idx_project_rules_type", "project_rules", ["rule_type"])
    op.create_index("idx_project_rules_severity", "project_rules", ["severity"])
    op.create_index("idx_project_rules_tags", "project_rules", ["tags"], postgresql_using="gin")
    op.create_index("idx_project_rules_active", "project_rules", ["is_active"], postgresql_where=sa.text("is_active = true"))

    # agent_profiles
    op.create_table(
        "agent_profiles",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            unique=True,
        ),
        sa.Column(
            "owner_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("target_agent", sa.String(100), nullable=False),
        sa.Column("max_context_tokens", sa.Integer(), nullable=False, server_default=sa.text("1500")),
        sa.Column("include_success_patterns", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("include_failure_patterns", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("include_project_rules", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("include_recent_usage", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("output_format", sa.String(50), nullable=False, server_default=sa.text("'markdown'")),
        sa.Column("template", sa.Text()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "idx_agent_profiles_owner_name",
        "agent_profiles",
        ["owner_id", "name"],
        unique=True,
    )

    # usage_events
    op.create_table(
        "usage_events",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "event_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            unique=True,
        ),
        sa.Column(
            "project_id",
            sa.BigInteger(),
            sa.ForeignKey("projects.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "user_id",
            sa.BigInteger(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("memory_type", sa.String(50), nullable=False),
        sa.Column("memory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query_text", sa.Text()),
        sa.Column("agent_profile", sa.String(100)),
        sa.Column("tokens_saved", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("retrieval_time_ms", sa.Integer()),
        sa.Column("was_useful", sa.Boolean()),
        sa.Column("was_modified", sa.Boolean()),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "memory_type IN ('success_pattern', 'failure_pattern', 'project_rule')",
            name="valid_memory_type",
        ),
        sa.CheckConstraint("tokens_saved >= 0", name="valid_usage_tokens"),
    )
    op.create_index("idx_usage_events_project", "usage_events", ["project_id"])
    op.create_index("idx_usage_events_user", "usage_events", ["user_id"])
    op.create_index("idx_usage_events_memory", "usage_events", ["memory_type", "memory_id"])
    op.create_index("idx_usage_events_created", "usage_events", [sa.text("created_at DESC")])

    # pattern_embeddings
    op.create_table(
        "pattern_embeddings",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "pattern_id",
            sa.BigInteger(),
            sa.ForeignKey("success_patterns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("embedding_provider", sa.String(50), nullable=False),
        sa.Column("embedding_model", sa.String(100), nullable=False),
        sa.Column("embedding_dim", sa.Integer(), nullable=False, server_default=sa.text("1536")),
        sa.Column("embedding_input_hash", sa.String(64), nullable=False),
        sa.Column("embedding_version", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "pattern_id",
            "embedding_provider",
            "embedding_model",
            "embedding_version",
            name="uq_pattern_embedding",
        ),
    )
    op.execute(
        """
        CREATE INDEX idx_pattern_embeddings_vector
        ON pattern_embeddings
        USING hnsw (embedding vector_cosine_ops);
        """
    )


def downgrade() -> None:
    op.drop_table("pattern_embeddings")
    op.drop_table("usage_events")
    op.drop_table("agent_profiles")
    op.drop_table("project_rules")
    op.drop_table("failure_patterns")
    op.drop_table("success_patterns")
    op.drop_table("projects")
    op.drop_table("users")
