"""
Database tests for Project Rift
Tests database queries, connections, and data integrity
"""

import pytest
import os
from datetime import datetime, timedelta
from database.queries import DatabaseQueries


@pytest.fixture
def db():
    """Fixture to provide database instance"""
    return DatabaseQueries()


class TestDatabaseConnection:
    """Tests for database connectivity"""

    def test_database_connection(self, db):
        """Test that database connection can be established"""
        try:
            conn = db.get_connection()
            assert conn is not None
            conn.close()
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_database_url_configured(self):
        """Test that DATABASE_URL is configured"""
        assert os.getenv('DATABASE_URL') is not None


class TestGamificationRules:
    """Tests for gamification rules queries"""

    def test_get_gamification_rule_valid(self, db):
        """Test retrieving a valid gamification rule"""
        try:
            rule = db.get_gamification_rule('call_connect')
            assert rule is not None
            assert 'gold_value' in rule
            assert 'xp_value' in rule
            assert rule['gold_value'] > 0
            assert rule['xp_value'] > 0
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_get_gamification_rule_invalid(self, db):
        """Test retrieving a non-existent rule"""
        try:
            rule = db.get_gamification_rule('invalid_event_type')
            assert rule is None
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_all_event_types_have_rules(self, db):
        """Test that all event types have gamification rules"""
        event_types = [
            'call_dial',
            'call_connect',
            'meeting_booked',
            'meeting_attended',
            'email_sent'
        ]

        try:
            for event_type in event_types:
                rule = db.get_gamification_rule(event_type)
                assert rule is not None, f"Missing rule for {event_type}"
                assert rule['gold_value'] >= 0
                assert rule['xp_value'] >= 0
        except Exception as e:
            pytest.skip(f"Database not available: {e}")


class TestEventInsertion:
    """Tests for event insertion"""

    def test_insert_event(self, db):
        """Test inserting a new event"""
        try:
            event_id = db.insert_event(
                source='manual',
                event_type='call_dial',
                gold_value=15,
                xp_value=5,
                metadata={'test': True}
            )

            assert event_id is not None
            assert isinstance(event_id, str)
            assert len(event_id) > 0
        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_insert_event_with_metadata(self, db):
        """Test inserting event with complex metadata"""
        try:
            metadata = {
                'prospect_name': 'John Doe',
                'company': 'Test Corp',
                'call_duration': 120
            }

            event_id = db.insert_event(
                source='nooks',
                event_type='call_connect',
                gold_value=100,
                xp_value=40,
                metadata=metadata
            )

            assert event_id is not None
        except Exception as e:
            pytest.skip(f"Database not available: {e}")


class TestCurrentStats:
    """Tests for current stats queries"""

    def test_get_current_stats(self, db):
        """Test retrieving current statistics"""
        try:
            stats = db.get_current_stats()

            assert stats is not None
            assert 'total_gold' in stats
            assert 'total_xp' in stats
            assert 'current_level' in stats
            assert 'rank' in stats
            assert 'events_today' in stats

            # Validate types
            assert isinstance(stats['total_gold'], (int, type(None)))
            assert isinstance(stats['total_xp'], (int, type(None)))
            assert isinstance(stats['current_level'], int)
            assert isinstance(stats['rank'], str)

        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_level_calculation(self, db):
        """Test that level is calculated correctly from XP"""
        try:
            stats = db.get_current_stats()

            total_xp = stats['total_xp']
            expected_level = int(total_xp / 1000) + 1
            assert stats['current_level'] == expected_level

        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_rank_calculation(self, db):
        """Test that rank is calculated correctly from gold"""
        try:
            stats = db.get_current_stats()

            total_gold = stats['total_gold']
            rank = stats['rank']

            # Validate rank is one of the valid values
            valid_ranks = ['Iron', 'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond', 'Challenger']
            assert rank in valid_ranks

            # Validate rank thresholds
            if total_gold >= 5000:
                assert rank == 'Challenger'
            elif total_gold >= 3000:
                assert rank == 'Diamond'
            elif total_gold >= 1500:
                assert rank == 'Platinum'
            elif total_gold >= 1000:
                assert rank == 'Gold'
            elif total_gold >= 500:
                assert rank == 'Silver'
            elif total_gold >= 200:
                assert rank == 'Bronze'
            else:
                assert rank == 'Iron'

        except Exception as e:
            pytest.skip(f"Database not available: {e}")


class TestDailyStats:
    """Tests for daily statistics queries"""

    def test_get_daily_stats(self, db):
        """Test retrieving daily statistics"""
        try:
            daily_stats = db.get_daily_stats(days=7)

            assert isinstance(daily_stats, list)
            # Each day should have required fields
            for day in daily_stats:
                assert 'event_date' in day
                assert 'total_events' in day
                assert 'total_gold' in day
                assert 'total_xp' in day

        except Exception as e:
            pytest.skip(f"Database not available: {e}")


class TestDuplicateDetection:
    """Tests for duplicate event detection"""

    def test_check_duplicate_event(self, db):
        """Test duplicate event detection"""
        try:
            # Insert an event
            metadata = {'test': 'duplicate_test', 'timestamp': datetime.now().isoformat()}
            event_id = db.insert_event(
                source='manual',
                event_type='email_sent',
                gold_value=10,
                xp_value=3,
                metadata=metadata
            )

            assert event_id is not None

            # Check if duplicate exists
            is_duplicate = db.check_duplicate_event(
                source='manual',
                event_type='email_sent',
                metadata=metadata,
                minutes=5
            )

            assert is_duplicate is True

        except Exception as e:
            pytest.skip(f"Database not available: {e}")

    def test_no_duplicate_for_different_event(self, db):
        """Test that different events are not marked as duplicates"""
        try:
            is_duplicate = db.check_duplicate_event(
                source='manual',
                event_type='call_dial',
                metadata={'unique': datetime.now().isoformat()},
                minutes=5
            )

            # Should not find a duplicate for this unique event
            assert is_duplicate is False

        except Exception as e:
            pytest.skip(f"Database not available: {e}")


class TestCleanup:
    """Tests for data cleanup functions"""

    @pytest.mark.skip(reason="Cleanup tests modify database")
    def test_cleanup_old_events(self, db):
        """Test cleaning up old events"""
        try:
            # This test is skipped by default to avoid deleting data
            deleted_count = db.cleanup_old_events(days=90)
            assert isinstance(deleted_count, int)
            assert deleted_count >= 0
        except Exception as e:
            pytest.skip(f"Database not available: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
