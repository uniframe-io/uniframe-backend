import time

import boto3  # type: ignore

from server.settings.global_sys_config import GLOBAL_CONFIG


# TODO: move this module into factory to generalize service for other cloud platform
class CloudWatchLogsHelper:
    def __init__(
        self,
        *,
        sort_ascending: bool,
        limit: int,
        start_timestamp: int,
        end_timestamp: int,
        region_name: str = GLOBAL_CONFIG.region,
    ):
        self.logs_client = boto3.client("logs", region_name=region_name)
        self.sort_ascending = sort_ascending
        self.limit = limit
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp

    def get_logs_by_log_stream(self, log_group: str, log_stream) -> str:
        query = f"""
        fields @timestamp, kubernetes.pod_name, log
        | filter @logStream like "{log_stream}"
        | sort @timestamp {'asc' if self.sort_ascending else 'desc'}
        | limit {self.limit}
        """
        start_query_response = self.logs_client.start_query(
            logGroupName=log_group,
            startTime=self.start_timestamp,
            endTime=self.end_timestamp,
            queryString=query,
        )
        query_id = start_query_response["queryId"]

        response = None

        # TODO: incremental load logs with pagination
        while response is None or response["status"] == "Running":
            time.sleep(1)
            response = self.logs_client.get_query_results(queryId=query_id)
        logs_list_nested = response["results"]
        logs_list = [
            {
                "timestamp": log[0]["value"],
                "pod_name": log[1]["value"],
                "log_text": log[2]["value"],
            }
            for log in logs_list_nested
        ]

        return sorted(logs_list, key=lambda k: k["timestamp"])
