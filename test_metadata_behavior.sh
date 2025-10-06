#!/bin/bash

# Metadata Behavior Test Script
# Tests that created_at is preserved and updated_at changes on updates

echo "🧪 Testing Metadata Behavior"
echo "=============================="

BASE_URL="http://127.0.0.1:8000"
TEST_USER="metadata-test-$(date +%s)"

echo "📝 Test 1: Create new item with simplified format"
echo "---------------------------------------------------"
echo "Creating item with initial features..."

# Create initial item
RESPONSE1=$(curl -s -X POST "$BASE_URL/items/$TEST_USER?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{"test_features": {"feature1": "initial_value", "feature2": 100}}')

echo "Response: $RESPONSE1"
echo ""

# Read the item to get initial timestamps
echo "Reading initial item..."
INITIAL_DATA=$(curl -s "$BASE_URL/get/item/$TEST_USER/test_features?table_type=bright_uid")
echo "Initial data: $INITIAL_DATA"
echo ""

# Extract timestamps
INITIAL_CREATED=$(echo $INITIAL_DATA | grep -o '"created_at":"[^"]*"' | cut -d'"' -f4)
INITIAL_UPDATED=$(echo $INITIAL_DATA | grep -o '"updated_at":"[^"]*"' | cut -d'"' -f4)

echo "Initial created_at: $INITIAL_CREATED"
echo "Initial updated_at: $INITIAL_UPDATED"
echo ""

echo "⏳ Waiting 3 seconds before update..."
sleep 3

echo ""
echo "📝 Test 2: Update existing item"
echo "-------------------------------"
echo "Updating item with new features..."

# Update the item
RESPONSE2=$(curl -s -X POST "$BASE_URL/items/$TEST_USER?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{"test_features": {"feature1": "updated_value", "feature2": 200, "feature3": "new_feature"}}')

echo "Response: $RESPONSE2"
echo ""

# Read the updated item
echo "Reading updated item..."
UPDATED_DATA=$(curl -s "$BASE_URL/get/item/$TEST_USER/test_features?table_type=bright_uid")
echo "Updated data: $UPDATED_DATA"
echo ""

# Extract updated timestamps
UPDATED_CREATED=$(echo $UPDATED_DATA | grep -o '"created_at":"[^"]*"' | cut -d'"' -f4)
UPDATED_UPDATED=$(echo $UPDATED_DATA | grep -o '"updated_at":"[^"]*"' | cut -d'"' -f4)

echo "Updated created_at: $UPDATED_CREATED"
echo "Updated updated_at: $UPDATED_UPDATED"
echo ""

echo "🔍 Test Results"
echo "==============="

# Check if created_at was preserved
if [ "$INITIAL_CREATED" = "$UPDATED_CREATED" ]; then
    echo "✅ PASS: created_at was preserved ($INITIAL_CREATED)"
else
    echo "❌ FAIL: created_at changed from $INITIAL_CREATED to $UPDATED_CREATED"
fi

# Check if updated_at changed
if [ "$INITIAL_UPDATED" != "$UPDATED_UPDATED" ]; then
    echo "✅ PASS: updated_at was updated ($INITIAL_UPDATED -> $UPDATED_UPDATED)"
else
    echo "❌ FAIL: updated_at did not change ($INITIAL_UPDATED)"
fi

echo ""
echo "📝 Test 3: Create new category for existing user"
echo "------------------------------------------------"
echo "Adding new category to existing user..."

# Add new category
RESPONSE3=$(curl -s -X POST "$BASE_URL/items/$TEST_USER?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{"new_category": {"featureA": "valueA", "featureB": 300}}')

echo "Response: $RESPONSE3"
echo ""

# Read the new category
echo "Reading new category..."
NEW_CATEGORY_DATA=$(curl -s "$BASE_URL/get/item/$TEST_USER/new_category?table_type=bright_uid")
echo "New category data: $NEW_CATEGORY_DATA"
echo ""

# Extract timestamps for new category
NEW_CREATED=$(echo $NEW_CATEGORY_DATA | grep -o '"created_at":"[^"]*"' | cut -d'"' -f4)
NEW_UPDATED=$(echo $NEW_CATEGORY_DATA | grep -o '"updated_at":"[^"]*"' | cut -d'"' -f4)

echo "New category created_at: $NEW_CREATED"
echo "New category updated_at: $NEW_UPDATED"
echo ""

# Check if new category has fresh timestamps
if [ "$NEW_CREATED" = "$NEW_UPDATED" ]; then
    echo "✅ PASS: New category has matching created_at and updated_at (fresh creation)"
else
    echo "❌ FAIL: New category timestamps don't match"
fi

echo ""
echo "📝 Test 4: Test with explicit metadata"
echo "-------------------------------------"
echo "Creating item with explicit metadata..."

# Create item with explicit metadata
EXPLICIT_USER="metadata-explicit-$(date +%s)"
RESPONSE4=$(curl -s -X POST "$BASE_URL/items/$EXPLICIT_USER?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{"user_features": {"data": {"age": 25, "income": 50000}, "metadata": {"created_at": "2025-10-06T08:00:00", "updated_at": "2025-10-06T08:00:00", "source": "ml_pipeline", "compute_id": "batch_001", "ttl": 3600}}}')

echo "Response: $RESPONSE4"
echo ""

# Read the explicit metadata item
echo "Reading explicit metadata item..."
EXPLICIT_DATA=$(curl -s "$BASE_URL/get/item/$EXPLICIT_USER/user_features?table_type=bright_uid")
echo "Explicit data: $EXPLICIT_DATA"
echo ""

# Extract explicit timestamps
EXPLICIT_CREATED=$(echo $EXPLICIT_DATA | grep -o '"created_at":"[^"]*"' | cut -d'"' -f4)
EXPLICIT_UPDATED=$(echo $EXPLICIT_DATA | grep -o '"updated_at":"[^"]*"' | cut -d'"' -f4)

echo "Explicit created_at: $EXPLICIT_CREATED"
echo "Explicit updated_at: $EXPLICIT_UPDATED"
echo ""

echo "⏳ Waiting 2 seconds before updating explicit metadata item..."
sleep 2

# Update the explicit metadata item
echo "Updating explicit metadata item..."
RESPONSE5=$(curl -s -X POST "$BASE_URL/items/$EXPLICIT_USER?table_type=bright_uid" \
  -H "Content-Type: application/json" \
  -d '{"user_features": {"data": {"age": 26, "income": 55000, "city": "New York"}, "metadata": {"created_at": "2025-10-06T08:00:00", "updated_at": "2025-10-06T08:00:00", "source": "ml_pipeline", "compute_id": "batch_001", "ttl": 3600}}}')

echo "Response: $RESPONSE5"
echo ""

# Read the updated explicit metadata item
echo "Reading updated explicit metadata item..."
UPDATED_EXPLICIT_DATA=$(curl -s "$BASE_URL/get/item/$EXPLICIT_USER/user_features?table_type=bright_uid")
echo "Updated explicit data: $UPDATED_EXPLICIT_DATA"
echo ""

# Extract updated explicit timestamps
UPDATED_EXPLICIT_CREATED=$(echo $UPDATED_EXPLICIT_DATA | grep -o '"created_at":"[^"]*"' | cut -d'"' -f4)
UPDATED_EXPLICIT_UPDATED=$(echo $UPDATED_EXPLICIT_DATA | grep -o '"updated_at":"[^"]*"' | cut -d'"' -f4)

echo "Updated explicit created_at: $UPDATED_EXPLICIT_CREATED"
echo "Updated explicit updated_at: $UPDATED_EXPLICIT_UPDATED"
echo ""

echo "🔍 Final Test Results"
echo "===================="

# Check if explicit created_at was preserved
if [ "$EXPLICIT_CREATED" = "$UPDATED_EXPLICIT_CREATED" ]; then
    echo "✅ PASS: Explicit created_at was preserved ($EXPLICIT_CREATED)"
else
    echo "❌ FAIL: Explicit created_at changed from $EXPLICIT_CREATED to $UPDATED_EXPLICIT_CREATED"
fi

# Check if explicit updated_at changed
if [ "$EXPLICIT_UPDATED" != "$UPDATED_EXPLICIT_UPDATED" ]; then
    echo "✅ PASS: Explicit updated_at was updated ($EXPLICIT_UPDATED -> $UPDATED_EXPLICIT_UPDATED)"
else
    echo "❌ FAIL: Explicit updated_at did not change ($EXPLICIT_UPDATED)"
fi

echo ""
echo "🎉 Metadata behavior test completed!"
echo "====================================="
