import os
from kubernetes import client, config
from logger import logger


class KubernetesEventTracker:
    def __init__(self):
        """
        Initializes KubernetesEventTracker with dynamic namespace and label selector.
        """
        try:
            self.namespace = os.getenv("KUBERNETES_NAMESPACE", "default")
            self.label_selector = os.getenv("LABEL_SELECTOR", "app=main-pod")
            config.load_incluster_config()
            self.v1 = client.CoreV1Api()
            logger.info(f"KubernetesEventTracker initialized for namespace='{self.namespace}' and label_selector='{self.label_selector}'.")
        except Exception as e:
            logger.error(f"Failed to initialize KubernetesEventTracker: {e}")
            raise

    def track_events(self):
        """
        Tracks Kubernetes events in the specified namespace and filters by label selector.

        :return: A list of filtered Kubernetes events.
        """
        try:
            events = self.v1.list_namespaced_event(namespace=self.namespace)
            logger.debug(f"Fetched {len(events.items)} events from namespace '{self.namespace}'.")
            tracked_events = []

            for event in events.items:
                # Filter events using label selector
                labels = self.get_labels_from_event(event)
                if not self.does_event_match_label_selector(labels, self.label_selector):
                    continue

                # Add the event to the list if it matches criteria
                tracked_event = {
                    "pod_name": event.involved_object.name,
                    "event_type": event.type,
                    "reason": event.reason,
                    "message": event.message,
                    "timestamp": event.last_timestamp
                }
                tracked_events.append(tracked_event)
                logger.debug(f"Tracked event: {tracked_event}")

            logger.info(f"Tracked {len(tracked_events)} events matching criteria.")
            return tracked_events
        except Exception as e:
            logger.error(f"Error tracking events: {e}")
            return []

    def track_main_pod_state(self):
        """
        Tracks the state of the Main Pod using the namespace and label selector.

        :return: A dictionary with the current state of the Main Pod.
        """
        try:
            pods = self.v1.list_namespaced_pod(namespace=self.namespace, label_selector=self.label_selector)
            main_pod_states = []

            for pod in pods.items:
                pod_state = {
                    "pod_name": pod.metadata.name,
                    "phase": pod.status.phase,  # Pod lifecycle phase (e.g., Running, Pending, Failed)
                    "conditions": {cond.type: cond.status for cond in pod.status.conditions or []},
                }
                main_pod_states.append(pod_state)
                logger.info(f"Tracked Main Pod state: {pod_state}")

            return main_pod_states
        except Exception as e:
            logger.error(f"Error tracking Main Pod state: {e}")
            return []

    def get_labels_from_event(self, event):
        """
        Extracts labels from the involved Kubernetes object of the event.

        :param event: The Kubernetes event object.
        :return: A dictionary of labels associated with the involved object.
        """
        try:
            resource = self.v1.read_namespaced_pod(
                name=event.involved_object.name, namespace=self.namespace
            )
            labels = resource.metadata.labels or {}
            logger.debug(f"Fetched labels for {event.involved_object.name}: {labels}")
            return labels
        except client.exceptions.ApiException as e:
            logger.warning(f"Failed to fetch labels for {event.involved_object.name}: {e}")
            return {}

    def does_event_match_label_selector(self, labels, label_selector):
        """
        Determines if a set of labels matches a given label selector.

        :param labels: A dictionary of labels (key-value pairs).
        :param label_selector: A label selector string (e.g., 'app=main-pod').
        :return: True if labels match the label selector, False otherwise.
        """
        try:
            selector_pairs = [pair.split("=") for pair in label_selector.split(",")]
            for key, value in selector_pairs:
                if labels.get(key) != value:
                    logger.debug(f"Label mismatch: key={key}, expected={value}, actual={labels.get(key)}")
                    return False
            return True
        except Exception as e:
            logger.error(f"Error matching label selector: {e}")
            return False
