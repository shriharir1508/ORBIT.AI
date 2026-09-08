from pathlib import Path
import sqlite3

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DB_PATH = PROJECT_ROOT / "database" / "orbit.db"

VECTOR_DB_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "vector_db"
)

COLLECTION_NAME = "orbit_rag"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class HybridRetriever:

    _embedding_model = None

    @classmethod
    def _get_embedding_model(cls):

        if cls._embedding_model is None:
            cls._embedding_model = SentenceTransformer(
                EMBEDDING_MODEL
            )

        return cls._embedding_model

    def __init__(self):

        if not DB_PATH.exists():
            raise FileNotFoundError(
                f"Database not found: {DB_PATH}"
            )

        if not VECTOR_DB_DIR.exists():
            raise FileNotFoundError(
                f"Vector database not found: {VECTOR_DB_DIR}"
            )

        self.connection = sqlite3.connect(
            DB_PATH
        )

        self.embedding_model = (
            self._get_embedding_model()
        )

        self.chroma_client = (
            chromadb.PersistentClient(
                path=str(VECTOR_DB_DIR)
            )
        )

        self.collection = (
            self.chroma_client.get_collection(
                name=COLLECTION_NAME
            )
        )

    def semantic_search(
        self,
        query,
        n_results=5
    ):

        query_embedding = (
            self.embedding_model
            .encode([query])
            .tolist()
        )

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n_results
        )

        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]

        output = []

        for index, document in enumerate(
            documents
        ):

            output.append({
                "text": document,
                "source_type":
                    metadatas[index].get(
                        "source_type"
                    ),
                "source_record_id":
                    metadatas[index].get(
                        "source_record_id"
                    ),
                "distance":
                    distances[index],
            })

        return output

    def branch_issues(
        self,
        branch_name
    ):

        rows = self.connection.execute(
            """
            SELECT
                s_no,
                issue,
                branch,
                link
            FROM issue_management
            WHERE LOWER(TRIM(branch))
                  = LOWER(TRIM(?))
            ORDER BY s_no
            """,
            (branch_name,)
        ).fetchall()

        return [
            {
                "source_type":
                    "operational_issue",
                "source_record_id":
                    str(row[0]),
                "branch":
                    row[2],
                "issue":
                    row[1],
                "link":
                    row[3],
            }
            for row in rows
        ]

    def high_risk_patients(
        self,
        branch_name=None,
        limit=None
    ):

        query = """
            SELECT
                rowid,
                branch,
                branch_city,
                disease,
                followup_risk,
                followup_status,
                contactability,
                remark
            FROM patient_followup
            WHERE LOWER(TRIM(followup_risk))
                  = 'high'
        """

        parameters = []

        if branch_name:

            query += """
                AND LOWER(TRIM(branch))
                    = LOWER(TRIM(?))
            """

            parameters.append(
                branch_name
            )

        query += """
            ORDER BY rowid
        """

        if limit is not None:

            query += """
                LIMIT ?
            """

            parameters.append(
                int(limit)
            )

        rows = self.connection.execute(
            query,
            parameters
        ).fetchall()

        return [
            {
                "source_type":
                    "patient_followup",
                "source_record_id":
                    str(row[0]),
                "branch":
                    row[1],
                "branch_city":
                    row[2],
                "disease":
                    row[3],
                "followup_risk":
                    row[4],
                "followup_status":
                    row[5],
                "contactability":
                    row[6],
                "remark":
                    row[7],
            }
            for row in rows
        ]

    def attrition_reasons(self):

        rows = self.connection.execute(
            """
            SELECT
                rank,
                patient_attrition_reason,
                reason_type,
                frequency
            FROM patient_attrition_reference
            ORDER BY rank
            """
        ).fetchall()

        return [
            {
                "source_type":
                    "patient_attrition_reference",
                "source_record_id":
                    str(row[0]),
                "reason":
                    row[1],
                "reason_type":
                    row[2],
                "frequency":
                    row[3],
            }
            for row in rows
        ]

    def sales_by_branch(
        self,
        branch_name=None
    ):

        if branch_name:

            rows = self.connection.execute(
                """
                SELECT
                    branch,
                    SUM(total_sales),
                    SUM(total_treatment),
                    SUM(total_medicine_sales)
                FROM sales
                WHERE LOWER(TRIM(branch))
                      = LOWER(TRIM(?))
                GROUP BY branch
                """,
                (branch_name,)
            ).fetchall()

        else:

            rows = self.connection.execute(
                """
                SELECT
                    branch,
                    SUM(total_sales),
                    SUM(total_treatment),
                    SUM(total_medicine_sales)
                FROM sales
                GROUP BY branch
                ORDER BY SUM(total_sales) DESC
                """
            ).fetchall()

        return [
            {
                "branch":
                    row[0],
                "total_sales":
                    row[1],
                "total_treatment":
                    row[2],
                "medicine_sales":
                    row[3],
            }
            for row in rows
        ]

    def marketing_summary(self):

        row = self.connection.execute(
            """
            SELECT
                COUNT(*),
                SUM(results),
                SUM(impressions),
                SUM(reach),
                SUM(total_amount)
            FROM marketing_campaign
            """
        ).fetchone()

        return {
            "campaign_records":
                row[0],
            "total_results":
                row[1],
            "total_impressions":
                row[2],
            "total_reach":
                row[3],
            "total_spend":
                row[4],
        }

    def close(self):

        self.connection.close()