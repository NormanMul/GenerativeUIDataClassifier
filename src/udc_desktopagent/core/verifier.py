"""UDC DesktopAgent — Post-action verification via screenshot diff."""

import structlog

logger = structlog.get_logger(__name__)


class ActionVerifier:
    """Verifies action success by comparing before/after screenshots.

    Uses screenshot diff analysis to confirm that the expected change
    occurred after an action was executed.
    """

    async def verify(
        self,
        before_screenshot: bytes,
        after_screenshot: bytes,
        expected_change: str,
    ) -> bool:
        """Verify that an action produced the expected screen change.

        Compares the before and after screenshots and evaluates whether
        the expected change description matches the observed difference.

        Args:
            before_screenshot: Screenshot captured before the action (PNG bytes).
            after_screenshot: Screenshot captured after the action (PNG bytes).
            expected_change: Natural language description of the expected change.

        Returns:
            True if the expected change was detected, False otherwise.

        Raises:
            NotImplementedError: Action verifier not yet implemented.
        """
        logger.info("verifier_verify", expected_change=expected_change)
        raise NotImplementedError("Action verifier not yet implemented")
