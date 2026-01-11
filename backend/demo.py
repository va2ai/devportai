"""
Demo script to test RAG ingestion and retrieval functionality.
Run this after starting the Docker containers.

Usage:
    python demo.py
"""

import asyncio
import httpx
import json
from pathlib import Path

# API endpoint
BASE_URL = "http://localhost:3000"

async def test_health():
    """Test health endpoint"""
    print("\n" + "="*60)
    print("Testing Health Endpoint")
    print("="*60)

    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")

        return response.status_code == 200


async def test_ingest():
    """Test document ingestion"""
    print("\n" + "="*60)
    print("Testing Document Ingestion")
    print("="*60)

    # Check if sample file exists
    sample_file = Path("sample_document.txt")
    if not sample_file.exists():
        print(f"❌ Sample file not found: {sample_file}")
        return None

    async with httpx.AsyncClient() as client:
        with open(sample_file, "rb") as f:
            files = {"file": (sample_file.name, f, "text/plain")}
            response = await client.post(
                f"{BASE_URL}/api/v1/ingest",
                files=files,
            )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Response:")
            print(json.dumps(data, indent=2))
            return data.get("document_id")
        else:
            print(f"Error: {response.text}")
            return None


async def test_retrieval(query: str = "machine learning"):
    """Test document retrieval"""
    print("\n" + "="*60)
    print(f"Testing Document Retrieval")
    print(f"Query: '{query}'")
    print("="*60)

    async with httpx.AsyncClient() as client:
        payload = {
            "query": query,
            "top_k": 3,
        }

        response = await client.post(
            f"{BASE_URL}/api/v1/retrieve",
            json=payload,
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"Query: {data['query']}")
            print(f"Results found: {data['result_count']}")

            if data["results"]:
                print("\nTop results:")
                for i, result in enumerate(data["results"], 1):
                    print(f"\n  Result {i}:")
                    print(f"    Document: {result['document_filename']}")
                    print(f"    Similarity: {result['similarity_score']:.4f}")
                    print(f"    Content: {result['content'][:100]}...")
            else:
                print("No results found")
        else:
            print(f"Error: {response.text}")


async def run_demo():
    """Run full demo"""
    print("\n" + "="*60)
    print("RAG Fact-Check API Demo")
    print("="*60)

    # Test health
    health_ok = await test_health()
    if not health_ok:
        print("\n❌ Health check failed. Is the server running?")
        print(f"Make sure to run: docker-compose up -d")
        return

    print("✅ Health check passed")

    # Test ingestion
    doc_id = await test_ingest()
    if doc_id is None:
        print("\n❌ Document ingestion failed")
        return

    print(f"✅ Document ingested (ID: {doc_id})")

    # Wait for embeddings to be generated
    print("\n⏳ Waiting for embeddings to be generated...")
    await asyncio.sleep(2)

    # Test retrieval
    queries = [
        "What is machine learning?",
        "supervised learning algorithms",
        "neural networks",
        "data preprocessing",
    ]

    for query in queries:
        await test_retrieval(query)
        # Small delay between requests
        await asyncio.sleep(0.5)

    print("\n" + "="*60)
    print("Demo completed!")
    print("="*60)
    print("\nNext steps:")
    print("1. Visit http://localhost:3000/docs for interactive API docs")
    print("2. Query the database directly to verify chunk storage:")
    print("   psql -h localhost -U postgres -d rag_db")
    print("   SELECT id, chunk_index, embedding FROM chunks LIMIT 5;")


if __name__ == "__main__":
    asyncio.run(run_demo())
