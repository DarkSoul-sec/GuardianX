"""Tests for the scan event hub used by the WebSocket endpoint."""

import asyncio
import unittest

from app.ws.hub import ScanEventHub


class ScanEventHubTests(unittest.IsolatedAsyncioTestCase):
    async def test_subscribe_receives_published_event(self) -> None:
        hub = ScanEventHub()
        hub.bind_loop(asyncio.get_running_loop())

        subscriber_id, queue = hub.subscribe()

        self.assertEqual(hub.subscriber_count, 1)

        hub.publish({"type": "scan.updated", "scan_id": 7, "status": "RUNNING"})

        event = await asyncio.wait_for(queue.get(), timeout=1)

        self.assertEqual(event["scan_id"], 7)
        self.assertEqual(event["status"], "RUNNING")

        hub.unsubscribe(subscriber_id)
        self.assertEqual(hub.subscriber_count, 0)

    async def test_publish_without_bound_loop_is_safe_noop(self) -> None:
        hub = ScanEventHub()
        hub.publish({"type": "scan.updated", "scan_id": 1})
        self.assertEqual(hub.subscriber_count, 0)

    async def test_multiple_subscribers_each_receive_events(self) -> None:
        hub = ScanEventHub()
        hub.bind_loop(asyncio.get_running_loop())

        _id_a, queue_a = hub.subscribe()
        _id_b, queue_b = hub.subscribe()

        hub.publish({"type": "scan.updated", "scan_id": 3})

        event_a = await asyncio.wait_for(queue_a.get(), timeout=1)
        event_b = await asyncio.wait_for(queue_b.get(), timeout=1)

        self.assertEqual(event_a, {"type": "scan.updated", "scan_id": 3})
        self.assertEqual(event_b, {"type": "scan.updated", "scan_id": 3})

    async def test_unsubscribe_stops_delivery(self) -> None:
        hub = ScanEventHub()
        hub.bind_loop(asyncio.get_running_loop())

        subscriber_id, queue = hub.subscribe()
        hub.unsubscribe(subscriber_id)

        hub.publish({"type": "scan.updated", "scan_id": 9})

        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(queue.get(), timeout=0.2)

    async def test_event_type_filter_restricts_delivery(self) -> None:
        hub = ScanEventHub()
        hub.bind_loop(asyncio.get_running_loop())

        _id, queue = hub.subscribe(event_types={"finding.updated"})

        hub.publish({"type": "scan.updated", "scan_id": 1})
        hub.publish({"type": "finding.updated", "finding_id": 5})

        event = await asyncio.wait_for(queue.get(), timeout=1)

        self.assertEqual(event["type"], "finding.updated")
        self.assertEqual(event["finding_id"], 5)

        with self.assertRaises(asyncio.TimeoutError):
            await asyncio.wait_for(queue.get(), timeout=0.2)

    async def test_unfiltered_subscriber_receives_all_events(self) -> None:
        hub = ScanEventHub()
        hub.bind_loop(asyncio.get_running_loop())

        _id, queue = hub.subscribe()

        hub.publish({"type": "scan.updated", "scan_id": 1})
        hub.publish({"type": "finding.updated", "finding_id": 2})

        first = await asyncio.wait_for(queue.get(), timeout=1)
        second = await asyncio.wait_for(queue.get(), timeout=1)

        self.assertEqual({first["type"], second["type"]}, {"scan.updated", "finding.updated"})


if __name__ == "__main__":
    unittest.main()
