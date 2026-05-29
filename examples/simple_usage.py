"""Simple usage example of BrokerGuard Field Verify."""

import asyncio
import base64
from pathlib import Path
import httpx


async def stamp_photo_example():
    """Example: Stamp a photo with GPS and upload to Supabase."""

    # Configuration
    API_URL = "http://localhost:8002"

    # Load sample image
    image_path = Path(__file__).parent / "sample_photo.jpg"

    if not image_path.exists():
        print(f"Error: Sample image not found at {image_path}")
        print("Please provide a sample_photo.jpg in the examples/ directory")
        return

    # Read and encode image
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image_base64 = base64.b64encode(image_bytes).decode()

    print("📸 Creating field verification...")
    print(f"   Image size: {len(image_bytes) / 1024:.1f} KB")

    # Prepare request
    request_data = {
        "image_base64": image_base64,
        "lat": -23.550520,  # São Paulo, Brazil
        "lon": -46.633308,
        "altitude": 760.5,
        "broker_id": "broker-example-123",
        "property_id": "PROP-EXAMPLE-456",
        "notes": "Example inspection from Python script",
    }

    # Call API
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.post(
                f"{API_URL}/field-verify/stamp",
                json=request_data
            )

            if response.status_code == 200:
                result = response.json()

                print("\n✅ Verification created successfully!")
                print(f"   Hash: {result['hash_sha256'][:32]}...")
                print(f"   PDF URL: {result['pdf_url']}")
                print(f"   Verification URL: {result['verification_url']}")
                print(f"\n   Metadata:")
                for key, value in result['metadata'].items():
                    print(f"     {key}: {value}")

                # Save stamped image
                stamped_base64 = result['stamped_image_base64']
                stamped_bytes = base64.b64decode(stamped_base64)

                output_path = Path(__file__).parent / "stamped_output.png"
                with open(output_path, "wb") as f:
                    f.write(stamped_bytes)

                print(f"\n💾 Stamped image saved to: {output_path}")

            else:
                print(f"❌ Error: {response.status_code}")
                print(response.text)

        except httpx.ConnectError:
            print("❌ Error: Could not connect to Field Verify service")
            print("   Make sure the service is running: uvicorn src.api:app --reload --port 8002")
        except Exception as e:
            print(f"❌ Error: {e}")


async def verify_hash_example():
    """Example: Verify a photo by hash."""

    API_URL = "http://localhost:8002"

    # Example hash (replace with real hash from previous verification)
    hash_value = "a" * 64  # Placeholder

    print(f"🔍 Verifying hash: {hash_value[:32]}...")

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{API_URL}/verify/{hash_value}")

            if response.status_code == 200:
                result = response.json()

                if result['valid']:
                    print("\n✅ Verification valid!")
                    print(f"   Timestamp: {result.get('timestamp')}")
                    print(f"   Location: {result.get('location')}")
                    print(f"   Broker ID: {result.get('broker_id')}")
                    print(f"   Property ID: {result.get('property_id')}")
                    print(f"   Image URL: {result.get('image_url')}")
                    print(f"   PDF URL: {result.get('pdf_url')}")
                else:
                    print("❌ Verification invalid or not found")
            else:
                print(f"❌ Error: {response.status_code}")

        except Exception as e:
            print(f"❌ Error: {e}")


async def main():
    """Main function."""
    print("=" * 60)
    print("BrokerGuard Field Verify - Usage Examples")
    print("=" * 60)
    print()

    # Example 1: Stamp photo
    await stamp_photo_example()

    print("\n" + "=" * 60)
    print()

    # Example 2: Verify hash
    # Uncomment to test verification:
    # await verify_hash_example()


if __name__ == "__main__":
    asyncio.run(main())
