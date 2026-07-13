# workers/deletion_worker.py

import asyncio

from sqlalchemy import select

from db.init_db import AsyncSessionLocal
from db.model_notes import PendingDeletion
from utils.s3_delete_object import delete_objects


async def process_pending_deletions():

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PendingDeletion).where(PendingDeletion.status == "pending")
        )

        pending = result.scalars().all()

        if not pending:
            return

        for item in pending:
            try:
                item.status = "processing"
                await session.commit()

                delete_objects([item.file_name])

                item.status = "completed"

                await session.commit()

                print(f"Deleted {item.file_name}")

            except Exception as exc:
                item.status = "failed"
                item.error_message = str(exc)

                await session.commit()

                print(f"Failed deleting {item.file_name}: {exc}")


async def main():

    print("Deletion worker started")

    while True:
        try:
            await process_pending_deletions()

        except Exception as exc:
            print(f"Worker error: {exc}")

        await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
