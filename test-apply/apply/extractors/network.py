"""
Network response extraction and analysis.
"""

from typing import List, Dict, Any, Optional


class NetworkExtractor:
    """Extracts structured data from network responses."""

    def __init__(self, logger):
        """
        Initialize network extractor.

        Args:
            logger: Logger instance
        """
        self.logger = logger

    def extract(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract useful information from network responses.

        Args:
            responses: List of captured network responses

        Returns:
            Extracted data summary
        """
        if not responses:
            return {}

        self.logger.debug(f"Analyzing {len(responses)} network responses")

        extracted = {
            'total_responses': len(responses),
            'urls': [],
            'job_data': [],
            'user_data': [],
            'form_data': [],
            'api_endpoints': []
        }

        for response in responses:
            url = response.get('url', '')
            data = response.get('data', {})

            extracted['urls'].append(url)

            # Look for job-related data
            if self._contains_job_data(data):
                extracted['job_data'].append({
                    'url': url,
                    'data': data
                })

            # Look for user/profile data
            if self._contains_user_data(data):
                extracted['user_data'].append({
                    'url': url,
                    'data': data
                })

            # Look for form schemas
            if self._contains_form_data(data):
                extracted['form_data'].append({
                    'url': url,
                    'data': data
                })

            # Identify API endpoints
            if self._is_api_endpoint(url):
                extracted['api_endpoints'].append(url)

        self.logger.debug(
            f"Network extraction: {len(extracted['job_data'])} job data, "
            f"{len(extracted['form_data'])} form schemas, "
            f"{len(extracted['api_endpoints'])} API endpoints"
        )

        return extracted

    def _contains_job_data(self, data: Any) -> bool:
        """Check if response contains job-related data."""
        if not isinstance(data, dict):
            return False

        job_keywords = [
            'job', 'position', 'title', 'company', 'salary',
            'description', 'requirements', 'posting'
        ]

        data_str = str(data).lower()
        return any(keyword in data_str for keyword in job_keywords)

    def _contains_user_data(self, data: Any) -> bool:
        """Check if response contains user/profile data."""
        if not isinstance(data, dict):
            return False

        user_keywords = [
            'user', 'profile', 'email', 'name', 'account',
            'authenticated', 'session'
        ]

        data_str = str(data).lower()
        return any(keyword in data_str for keyword in user_keywords)

    def _contains_form_data(self, data: Any) -> bool:
        """Check if response contains form schema/structure."""
        if not isinstance(data, dict):
            return False

        form_keywords = [
            'form', 'field', 'input', 'question', 'schema',
            'required', 'validation'
        ]

        data_str = str(data).lower()
        return any(keyword in data_str for keyword in form_keywords)

    def _is_api_endpoint(self, url: str) -> bool:
        """Check if URL looks like an API endpoint."""
        api_indicators = [
            '/api/', '/graphql', '/v1/', '/v2/', '/rest/',
            '/_next/data/', '/trpc/'
        ]

        return any(indicator in url.lower() for indicator in api_indicators)

    def get_application_status(self, responses: List[Dict[str, Any]]) -> Optional[str]:
        """
        Try to determine application status from network responses.

        Args:
            responses: List of network responses

        Returns:
            Status string if found, None otherwise
        """
        for response in responses:
            data = response.get('data', {})
            url = response.get('url', '').lower()

            # Look for status indicators
            if isinstance(data, dict):
                # Only consider application-related endpoints
                is_application_related = any(keyword in url for keyword in [
                    'application', 'apply', 'submit', 'candidate', 'job'
                ])

                # Check common status fields
                for key in ['status', 'application_status', 'applicationStatus', 'state']:
                    if key in data:
                        status = str(data[key]).lower()
                        # Only treat as success if it's application-related
                        if is_application_related and status in ['submitted', 'complete', 'success', 'accepted']:
                            return status.upper()

                # Check for success indicators - must be application-related
                if is_application_related:
                    if data.get('submitted') is True:
                        return 'SUBMITTED'
                    if data.get('applicationSubmitted') is True:
                        return 'SUBMITTED'

        return None
