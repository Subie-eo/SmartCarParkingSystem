from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta

from .models import ParkingSlot, Booking


class BookingLeaveFlowTests(TestCase):
	def setUp(self):
		User = get_user_model()
		# Create a driver user
		self.user = User.objects.create_user(
			email='driver@example.com',
			username='driver',
			phone_number='254700000001',
			vehicle_plate='ABC-123',
			password='pass'
		)

		# Create an admin user
		self.admin = User.objects.create_superuser(
			email='admin@example.com',
			username='admin',
			phone_number='254700000002',
			vehicle_plate='ADM-1',
			password='pass'
		)

		# Create two parking slots
		self.slot1 = ParkingSlot.objects.create(slot_id='A-1', slot_name='A1', level='1')
		self.slot2 = ParkingSlot.objects.create(slot_id='A-2', slot_name='A2', level='1')

		self.client = Client()

	def test_user_blocked_when_active_paid_and_slot_still_occupied(self):
		now = timezone.now()
		# Create a paid booking and mark slot occupied
		booking = Booking.objects.create(
			user=self.user,
			slot=self.slot1,
			start_time=now,
			end_time=now + timedelta(hours=2),
			payment_status=Booking.STATUS_PAID
		)
		self.slot1.is_occupied = True
		self.slot1.save()

		# User tries to book another slot -> should NOT create a new booking
		self.client.force_login(self.user)
		start = (now + timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M')
		resp = self.client.post(reverse('parking:initiate_booking', args=[self.slot2.slot_id]), {
			'start_time': start,
			'duration_hours': '2'
		})

		# No booking for slot2 created for this user
		self.assertFalse(Booking.objects.filter(user=self.user, slot=self.slot2).exists())

	def test_admin_free_allows_user_to_book_and_leave_endpoint_frees_slot(self):
		now = timezone.now()
		# Create a paid booking and mark slot occupied
		booking = Booking.objects.create(
			user=self.user,
			slot=self.slot1,
			start_time=now,
			end_time=now + timedelta(hours=2),
			payment_status=Booking.STATUS_PAID
		)
		self.slot1.is_occupied = True
		self.slot1.save()

		# Admin frees the slot (simulate admin action)
		self.slot1.is_occupied = False
		self.slot1.save()

		# Now user should be able to initiate booking for slot2
		self.client.force_login(self.user)
		start = (now + timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M')
		resp = self.client.post(reverse('parking:initiate_booking', args=[self.slot2.slot_id]), {
			'start_time': start,
			'duration_hours': '2'
		})

		self.assertTrue(Booking.objects.filter(user=self.user, slot=self.slot2).exists())

		# Simulate marking the new booking as PAID and occupying the slot
		new_booking = Booking.objects.get(user=self.user, slot=self.slot2)
		new_booking.payment_status = Booking.STATUS_PAID
		new_booking.save()
		self.slot2.is_occupied = True
		self.slot2.save()

		# User uses leave endpoint to free the slot
		resp = self.client.post(reverse('parking:leave_slot'))
		self.slot2.refresh_from_db()
		new_booking.refresh_from_db()

		self.assertFalse(self.slot2.is_occupied)
		# end_time should be approximately now (not None)
		self.assertIsNotNone(new_booking.end_time)

	def test_simulate_payment_marks_paid_and_occupies_slot(self):
		now = timezone.now()
		# Create a pending booking
		booking = Booking.objects.create(
			user=self.user,
			slot=self.slot1,
			start_time=now,
			end_time=now + timedelta(hours=1),
			payment_status=Booking.STATUS_PENDING
		)

		# Admin posts to simulate endpoint
		self.client.force_login(self.admin)
		resp = self.client.post(reverse('parking:simulate_booking_payment', args=[booking.id]))

		booking.refresh_from_db()
		self.slot1.refresh_from_db()
		self.assertEqual(booking.payment_status, Booking.STATUS_PAID)
		self.assertTrue(self.slot1.is_occupied)

	def test_leave_undo_restores_slot_and_clears_session(self):
		now = timezone.now()
		booking = Booking.objects.create(
			user=self.user,
			slot=self.slot1,
			start_time=now,
			end_time=now + timedelta(hours=1),
			payment_status=Booking.STATUS_PAID
		)
		self.slot1.is_occupied = True
		self.slot1.save()

		self.client.force_login(self.user)
		resp = self.client.post(reverse('parking:leave_slot'))
		# session should have last_leave
		session = self.client.session
		self.assertIn('last_leave', session)

		# Undo
		resp = self.client.post(reverse('parking:undo_leave'))
		self.slot1.refresh_from_db()
		booking.refresh_from_db()
		self.assertTrue(self.slot1.is_occupied)
		self.assertNotIn('last_leave', self.client.session)
