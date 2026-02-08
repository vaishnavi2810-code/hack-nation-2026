"""
CallPilot API Endpoint Tests

Run with: python3 tests/test_endpoints.py

Make sure the server is running: python3 -m uvicorn main:app --reload --port 8000
"""

import requests
from datetime import datetime, timedelta
import json
import time

BASE_URL = "http://localhost:8000"

# Store data between tests
test_data = {
    "appointment_id": None,
    "available_slot": None,
    "second_slot": None
}


def print_result(test_name: str, passed: bool, details: str = None, error: str = None):
    """Pretty print test results."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status} | {test_name}")
    if details:
        print(f"   → {details}")
    if error:
        print(f"   ✗ Error: {error}")


def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"   {title}")
    print('='*60)


# ============== Health & Status Tests ==============

def test_health_check():
    """Test: Health check endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        data = response.json()
        passed = response.status_code == 200 and data.get("status") == "healthy"
        print_result("Health Check", passed, f"Status: {data.get('status')}")
        return passed
    except Exception as e:
        print_result("Health Check", False, error=str(e))
        return False


def test_root_endpoint():
    """Test: Root endpoint returns API info"""
    try:
        response = requests.get(f"{BASE_URL}/")
        data = response.json()
        passed = response.status_code == 200 and "service" in data
        print_result("Root Endpoint", passed, f"Service: {data.get('service')}")
        return passed
    except Exception as e:
        print_result("Root Endpoint", False, error=str(e))
        return False


def test_calendar_status_connected():
    """Test: Calendar should be connected"""
    try:
        response = requests.get(f"{BASE_URL}/api/calendar/status")
        data = response.json()
        passed = response.status_code == 200 and data.get("connected") == True
        print_result(
            "Calendar Status (Connected)", 
            passed, 
            f"Email: {data.get('email')}" if passed else "Not connected!"
        )
        return passed
    except Exception as e:
        print_result("Calendar Status", False, error=str(e))
        return False


def test_get_auth_url():
    """Test: Get OAuth URL (should return valid Google URL)"""
    try:
        response = requests.get(f"{BASE_URL}/api/calendar/auth-url")
        data = response.json()
        passed = (
            response.status_code == 200 and 
            "auth_url" in data and 
            "accounts.google.com" in data.get("auth_url", "")
        )
        print_result("Get Auth URL", passed, "Valid Google OAuth URL returned")
        return passed
    except Exception as e:
        print_result("Get Auth URL", False, error=str(e))
        return False


# ============== Availability Tests ==============

def test_availability_today():
    """Test: Check availability for today"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/calendar/check-availability",
            json={"date": "today"}
        )
        data = response.json()
        passed = response.status_code == 200 and "available_slots" in data
        print_result(
            "Availability - Today", 
            passed, 
            f"{data.get('total_slots')} slots on {data.get('formatted_date')}"
        )
        return passed
    except Exception as e:
        print_result("Availability - Today", False, error=str(e))
        return False


def test_availability_tomorrow():
    """Test: Check availability for tomorrow and store slots for later tests"""
    global test_data
    try:
        response = requests.post(
            f"{BASE_URL}/api/calendar/check-availability",
            json={"date": "tomorrow"}
        )
        data = response.json()
        passed = response.status_code == 200 and len(data.get("available_slots", [])) > 0
        
        if passed:
            # Store first and second slots for later tests
            slots = data.get("available_slots", [])
            test_data["available_slot"] = slots[0] if len(slots) > 0 else None
            test_data["second_slot"] = slots[1] if len(slots) > 1 else None
        
        print_result(
            "Availability - Tomorrow", 
            passed, 
            f"{data.get('total_slots')} slots available"
        )
        return passed
    except Exception as e:
        print_result("Availability - Tomorrow", False, error=str(e))
        return False


def test_availability_natural_language():
    """Test: Check availability using natural language dates"""
    try:
        dates_to_test = ["next monday", "next tuesday", "next wednesday"]
        all_passed = True
        
        for date in dates_to_test:
            response = requests.post(
                f"{BASE_URL}/api/calendar/check-availability",
                json={"date": date}
            )
            if response.status_code != 200:
                all_passed = False
                break
        
        print_result(
            "Availability - Natural Language", 
            all_passed, 
            f"Tested: {', '.join(dates_to_test)}"
        )
        return all_passed
    except Exception as e:
        print_result("Availability - Natural Language", False, error=str(e))
        return False


def test_availability_specific_date():
    """Test: Check availability for specific date format (YYYY-MM-DD)"""
    try:
        future_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        response = requests.post(
            f"{BASE_URL}/api/calendar/check-availability",
            json={"date": future_date}
        )
        data = response.json()
        passed = response.status_code == 200 and data.get("date") == future_date
        print_result(
            "Availability - Specific Date (YYYY-MM-DD)", 
            passed, 
            f"Date: {future_date}, Slots: {data.get('total_slots')}"
        )
        return passed
    except Exception as e:
        print_result("Availability - Specific Date", False, error=str(e))
        return False


def test_availability_past_date():
    """Test: Past date should return no slots"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/calendar/check-availability",
            json={"date": "2020-01-01"}
        )
        data = response.json()
        passed = response.status_code == 200 and data.get("total_slots") == 0
        print_result(
            "Availability - Past Date (should be empty)", 
            passed, 
            f"Message: {data.get('message')}"
        )
        return passed
    except Exception as e:
        print_result("Availability - Past Date", False, error=str(e))
        return False


def test_availability_range():
    """Test: Check availability for multiple dates at once"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/calendar/check-availability-range",
            json={"dates": ["tomorrow", "next monday", "next tuesday"]}
        )
        data = response.json()
        passed = (
            response.status_code == 200 and 
            "dates" in data and 
            len(data.get("dates", [])) == 3
        )
        print_result(
            "Availability - Range (3 dates)", 
            passed, 
            f"Total slots across all dates: {data.get('total_slots')}"
        )
        return passed
    except Exception as e:
        print_result("Availability - Range", False, error=str(e))
        return False


def test_availability_custom_duration():
    """Test: Check availability with custom duration"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/calendar/check-availability",
            json={"date": "tomorrow", "duration_minutes": 60}
        )
        data = response.json()
        passed = response.status_code == 200 and "available_slots" in data
        print_result(
            "Availability - Custom Duration (60 min)", 
            passed, 
            f"Slots: {data.get('total_slots')} (fewer due to longer duration)"
        )
        return passed
    except Exception as e:
        print_result("Availability - Custom Duration", False, error=str(e))
        return False


# ============== Appointment CRUD Tests ==============

def test_create_appointment():
    """Test: Create a new appointment using stored slot"""
    global test_data
    try:
        if not test_data.get("available_slot"):
            print_result("Create Appointment", False, error="No available slot from previous test")
            return False
        
        slot = test_data["available_slot"]
        
        response = requests.post(
            f"{BASE_URL}/api/calendar/appointments",
            json={
                "patient_name": "John Doe",
                "patient_phone": "+1234567890",
                "patient_email": "john.doe@example.com",
                "appointment_datetime": slot["start"],
                "appointment_type": "checkup",
                "notes": "Test appointment - API testing"
            }
        )
        data = response.json()
        passed = response.status_code == 200 and data.get("success") == True
        
        if passed:
            test_data["appointment_id"] = data.get("confirmation_id")
            apt = data.get("appointment", {})
            print_result(
                "Create Appointment", 
                passed, 
                f"ID: {test_data['appointment_id']}, Time: {apt.get('formatted_time')}"
            )
        else:
            print_result("Create Appointment", False, error=data.get("detail", "Unknown error"))
        
        return passed
    except Exception as e:
        print_result("Create Appointment", False, error=str(e))
        return False


def test_create_duplicate_appointment():
    """Test: Creating appointment at same time should fail"""
    global test_data
    try:
        if not test_data.get("available_slot"):
            print_result("Create Duplicate (should fail)", False, error="No slot data")
            return False
        
        slot = test_data["available_slot"]
        
        response = requests.post(
            f"{BASE_URL}/api/calendar/appointments",
            json={
                "patient_name": "Jane Smith",
                "patient_phone": "+0987654321",
                "appointment_datetime": slot["start"],
                "appointment_type": "consultation"
            }
        )
        
        # Should fail with 400
        passed = response.status_code == 400
        print_result(
            "Create Duplicate Appointment (should fail)", 
            passed, 
            "Correctly rejected duplicate booking" if passed else "Should have been rejected!"
        )
        return passed
    except Exception as e:
        print_result("Create Duplicate", False, error=str(e))
        return False


def test_get_appointment_by_id():
    """Test: Retrieve the created appointment by ID"""
    global test_data
    try:
        if not test_data.get("appointment_id"):
            print_result("Get Appointment by ID", False, error="No appointment ID")
            return False
        
        response = requests.get(
            f"{BASE_URL}/api/calendar/appointments/{test_data['appointment_id']}"
        )
        data = response.json()
        passed = (
            response.status_code == 200 and 
            data.get("success") == True and
            data.get("appointment", {}).get("patient", {}).get("name") == "John Doe"
        )
        
        if passed:
            apt = data.get("appointment", {})
            print_result(
                "Get Appointment by ID", 
                passed, 
                f"Patient: {apt.get('patient', {}).get('name')}, Status: {apt.get('status')}"
            )
        else:
            print_result("Get Appointment by ID", False, error="Data mismatch")
        
        return passed
    except Exception as e:
        print_result("Get Appointment by ID", False, error=str(e))
        return False


def test_get_appointment_not_found():
    """Test: Getting non-existent appointment should return 404"""
    try:
        response = requests.get(
            f"{BASE_URL}/api/calendar/appointments/fake-id-that-does-not-exist-12345"
        )
        passed = response.status_code == 404
        print_result(
            "Get Appointment - Not Found (expect 404)", 
            passed, 
            "Correctly returned 404" if passed else f"Got {response.status_code}"
        )
        return passed
    except Exception as e:
        print_result("Get Appointment - Not Found", False, error=str(e))
        return False


def test_get_upcoming_appointments():
    """Test: List upcoming appointments (should include our created one)"""
    global test_data
    try:
        response = requests.get(f"{BASE_URL}/api/calendar/appointments")
        data = response.json()
        
        # Check if our appointment is in the list
        our_apt_found = False
        if test_data.get("appointment_id"):
            for apt in data.get("appointments", []):
                if apt.get("id") == test_data["appointment_id"]:
                    our_apt_found = True
                    break
        
        passed = response.status_code == 200 and our_apt_found
        print_result(
            "Get Upcoming Appointments", 
            passed, 
            f"Total: {data.get('total')}, Our appointment found: {our_apt_found}"
        )
        return passed
    except Exception as e:
        print_result("Get Upcoming Appointments", False, error=str(e))
        return False


def test_get_upcoming_with_hours_filter():
    """Test: Get appointments within specific hours"""
    try:
        response = requests.get(f"{BASE_URL}/api/calendar/appointments?hours_ahead=48")
        data = response.json()
        passed = response.status_code == 200 and "appointments" in data
        print_result(
            "Get Upcoming (48 hours filter)", 
            passed, 
            f"Found {data.get('total')} appointments in next 48 hours"
        )
        return passed
    except Exception as e:
        print_result("Get Upcoming (filtered)", False, error=str(e))
        return False


def test_reschedule_appointment():
    """Test: Reschedule appointment to a different time"""
    global test_data
    try:
        if not test_data.get("appointment_id"):
            print_result("Reschedule Appointment", False, error="No appointment ID")
            return False
        
        if not test_data.get("second_slot"):
            print_result("Reschedule Appointment", False, error="No second slot available")
            return False
        
        new_slot = test_data["second_slot"]
        
        response = requests.patch(
            f"{BASE_URL}/api/calendar/appointments/{test_data['appointment_id']}",
            json={"new_datetime": new_slot["start"]}
        )
        data = response.json()
        passed = response.status_code == 200 and data.get("success") == True
        
        if passed:
            apt = data.get("appointment", {})
            print_result(
                "Reschedule Appointment", 
                passed, 
                f"New time: {apt.get('formatted_time')} on {apt.get('formatted_date')}"
            )
        else:
            print_result("Reschedule Appointment", False, error=data.get("detail", "Unknown"))
        
        return passed
    except Exception as e:
        print_result("Reschedule Appointment", False, error=str(e))
        return False


def test_reschedule_to_unavailable_slot():
    """Test: Rescheduling to unavailable slot should fail"""
    global test_data
    try:
        if not test_data.get("appointment_id"):
            print_result("Reschedule to Unavailable (should fail)", False, error="No appointment")
            return False
        
        # Try to reschedule to a past date
        past_time = "2020-01-01T10:00:00-05:00"
        
        response = requests.patch(
            f"{BASE_URL}/api/calendar/appointments/{test_data['appointment_id']}",
            json={"new_datetime": past_time}
        )
        
        passed = response.status_code == 400
        print_result(
            "Reschedule to Unavailable Slot (should fail)", 
            passed, 
            "Correctly rejected" if passed else "Should have been rejected!"
        )
        return passed
    except Exception as e:
        print_result("Reschedule to Unavailable", False, error=str(e))
        return False


# ============== Reminder & No-Show Tests ==============

def test_mark_reminder_sent():
    """Test: Mark reminder as sent"""
    global test_data
    try:
        if not test_data.get("appointment_id"):
            print_result("Mark Reminder Sent", False, error="No appointment ID")
            return False
        
        response = requests.patch(
            f"{BASE_URL}/api/calendar/appointments/{test_data['appointment_id']}/remind"
        )
        data = response.json()
        passed = response.status_code == 200 and data.get("reminder_sent") == True
        print_result(
            "Mark Reminder Sent", 
            passed, 
            f"Reminder sent: {data.get('reminder_sent')}"
        )
        return passed
    except Exception as e:
        print_result("Mark Reminder Sent", False, error=str(e))
        return False


def test_verify_reminder_status():
    """Test: Verify reminder status was updated in appointment"""
    global test_data
    try:
        if not test_data.get("appointment_id"):
            print_result("Verify Reminder Status", False, error="No appointment ID")
            return False
        
        response = requests.get(
            f"{BASE_URL}/api/calendar/appointments/{test_data['appointment_id']}"
        )
        data = response.json()
        apt = data.get("appointment", {})
        passed = apt.get("reminder_sent") == True
        print_result(
            "Verify Reminder Status Updated", 
            passed, 
            f"reminder_sent = {apt.get('reminder_sent')}"
        )
        return passed
    except Exception as e:
        print_result("Verify Reminder Status", False, error=str(e))
        return False


def test_mark_no_show():
    """Test: Mark appointment as no-show"""
    global test_data
    try:
        if not test_data.get("appointment_id"):
            print_result("Mark No-Show", False, error="No appointment ID")
            return False
        
        response = requests.patch(
            f"{BASE_URL}/api/calendar/appointments/{test_data['appointment_id']}/no-show"
        )
        data = response.json()
        passed = response.status_code == 200 and data.get("status") == "no_show"
        print_result(
            "Mark No-Show", 
            passed, 
            f"Status changed to: {data.get('status')}"
        )
        return passed
    except Exception as e:
        print_result("Mark No-Show", False, error=str(e))
        return False


def test_verify_no_show_status():
    """Test: Verify no-show status was updated"""
    global test_data
    try:
        if not test_data.get("appointment_id"):
            print_result("Verify No-Show Status", False, error="No appointment ID")
            return False
        
        response = requests.get(
            f"{BASE_URL}/api/calendar/appointments/{test_data['appointment_id']}"
        )
        data = response.json()
        apt = data.get("appointment", {})
        passed = apt.get("status") == "no_show"
        print_result(
            "Verify No-Show Status Updated", 
            passed, 
            f"status = {apt.get('status')}"
        )
        return passed
    except Exception as e:
        print_result("Verify No-Show Status", False, error=str(e))
        return False


# ============== Cancel Tests ==============

def test_cancel_appointment():
    """Test: Cancel the appointment"""
    global test_data
    try:
        if not test_data.get("appointment_id"):
            print_result("Cancel Appointment", False, error="No appointment ID")
            return False
        
        response = requests.delete(
            f"{BASE_URL}/api/calendar/appointments/{test_data['appointment_id']}"
        )
        data = response.json()
        passed = response.status_code == 200 and data.get("success") == True
        print_result(
            "Cancel Appointment", 
            passed, 
            f"Message: {data.get('message')}"
        )
        return passed
    except Exception as e:
        print_result("Cancel Appointment", False, error=str(e))
        return False


def test_verify_cancelled_status():
    """Test: Verify appointment shows as cancelled"""
    global test_data
    try:
        if not test_data.get("appointment_id"):
            print_result("Verify Cancelled Status", False, error="No appointment ID")
            return False
        
        response = requests.get(
            f"{BASE_URL}/api/calendar/appointments/{test_data['appointment_id']}"
        )
        data = response.json()
        apt = data.get("appointment", {})
        passed = apt.get("status") == "cancelled"
        print_result(
            "Verify Cancelled Status", 
            passed, 
            f"status = {apt.get('status')}"
        )
        return passed
    except Exception as e:
        print_result("Verify Cancelled Status", False, error=str(e))
        return False


def test_cancel_nonexistent():
    """Test: Cancelling non-existent appointment should fail"""
    try:
        response = requests.delete(
            f"{BASE_URL}/api/calendar/appointments/fake-id-12345"
        )
        passed = response.status_code in [400, 404]
        print_result(
            "Cancel Non-existent (should fail)", 
            passed, 
            f"Correctly returned {response.status_code}" if passed else "Should have failed"
        )
        return passed
    except Exception as e:
        print_result("Cancel Non-existent", False, error=str(e))
        return False


# ============== Events Tests ==============

def test_get_calendar_events():
    """Test: Get raw calendar events"""
    try:
        response = requests.get(f"{BASE_URL}/api/calendar/events")
        data = response.json()
        passed = response.status_code == 200 and "events" in data
        print_result(
            "Get Calendar Events", 
            passed, 
            f"Total events: {data.get('total')}"
        )
        return passed
    except Exception as e:
        print_result("Get Calendar Events", False, error=str(e))
        return False


def test_get_events_with_time_filter():
    """Test: Get events with time filter"""
    try:
        time_min = datetime.now().isoformat()
        time_max = (datetime.now() + timedelta(days=7)).isoformat()
        
        response = requests.get(
            f"{BASE_URL}/api/calendar/events",
            params={"time_min": time_min, "time_max": time_max}
        )
        data = response.json()
        passed = response.status_code == 200 and "events" in data
        print_result(
            "Get Events (7-day filter)", 
            passed, 
            f"Events in next 7 days: {data.get('total')}"
        )
        return passed
    except Exception as e:
        print_result("Get Events (filtered)", False, error=str(e))
        return False


# ============== Run All Tests ==============

def run_all_tests():
    """Run all tests in logical sequence."""
    
    print("\n" + "=" * 60)
    print("   🏥 CallPilot API - Comprehensive Endpoint Tests")
    print("=" * 60)
    
    results = []
    
    # Health & Status
    print_section("Health & Status")
    results.append(("Health Check", test_health_check()))
    results.append(("Root Endpoint", test_root_endpoint()))
    results.append(("Calendar Connected", test_calendar_status_connected()))
    results.append(("Get Auth URL", test_get_auth_url()))
    
    # Availability
    print_section("Availability Checks")
    results.append(("Availability - Today", test_availability_today()))
    results.append(("Availability - Tomorrow", test_availability_tomorrow()))
    results.append(("Availability - Natural Language", test_availability_natural_language()))
    results.append(("Availability - Specific Date", test_availability_specific_date()))
    results.append(("Availability - Past Date", test_availability_past_date()))
    results.append(("Availability - Range", test_availability_range()))
    results.append(("Availability - Custom Duration", test_availability_custom_duration()))
    
    # Appointment CRUD
    print_section("Appointment CRUD")
    results.append(("Create Appointment", test_create_appointment()))
    results.append(("Create Duplicate (fail)", test_create_duplicate_appointment()))
    results.append(("Get Appointment by ID", test_get_appointment_by_id()))
    results.append(("Get Appointment - 404", test_get_appointment_not_found()))
    results.append(("Get Upcoming Appointments", test_get_upcoming_appointments()))
    results.append(("Get Upcoming (filtered)", test_get_upcoming_with_hours_filter()))
    results.append(("Reschedule Appointment", test_reschedule_appointment()))
    results.append(("Reschedule to Unavailable (fail)", test_reschedule_to_unavailable_slot()))
    
    # Reminder & No-Show
    print_section("Reminder & No-Show")
    results.append(("Mark Reminder Sent", test_mark_reminder_sent()))
    results.append(("Verify Reminder Status", test_verify_reminder_status()))
    results.append(("Mark No-Show", test_mark_no_show()))
    results.append(("Verify No-Show Status", test_verify_no_show_status()))
    
    # Cancel
    print_section("Cancel Appointment")
    results.append(("Cancel Appointment", test_cancel_appointment()))
    results.append(("Verify Cancelled Status", test_verify_cancelled_status()))
    results.append(("Cancel Non-existent (fail)", test_cancel_nonexistent()))
    
    # Events
    print_section("Calendar Events")
    results.append(("Get Calendar Events", test_get_calendar_events()))
    results.append(("Get Events (filtered)", test_get_events_with_time_filter()))
    
    # Summary
    print("\n" + "=" * 60)
    print("   📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, p in results if p)
    failed = sum(1 for _, p in results if not p)
    total = len(results)
    
    print(f"\n   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📝 Total:  {total}")
    
    if failed > 0:
        print(f"\n   Failed tests:")
        for name, result in results:
            if not result:
                print(f"      ✗ {name}")
    
    print(f"\n   {'🎉 ALL TESTS PASSED!' if failed == 0 else '⚠️  Some tests failed'}")
    print("=" * 60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    run_all_tests()