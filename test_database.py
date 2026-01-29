from database import DatabaseManager

print("[TEST] Testing database creation...")
db = DatabaseManager()
print("[TEST] ✅ Database created successfully!")

# Test basic operations
print("\n[TEST] Testing client creation...")
client = db.get_or_create_client(
    client_id="test_client_123",
    system_info={"hostname": "test-pc", "platform": "Windows"},
    ip_address="192.168.1.100"
)
print(f"[TEST] ✅ Client created: {client.client_id}")

# Get stats
stats = db.get_statistics()
print(f"\n[TEST] ✅ Statistics: {stats}")

# Cleanup
db.close()
print("\n[TEST] ✅ All tests passed!")
