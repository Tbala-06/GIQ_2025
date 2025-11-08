#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Robot State Module
State machine for robot control with valid state transitions.
"""

import time
from enum import Enum
from typing import Callable, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class RobotState(Enum):
    """Robot operational states"""
    IDLE = "idle"
    MOVING = "moving"
    POSITIONING = "positioning"
    PAINTING = "painting"
    COMPLETED = "completed"
    ERROR = "error"


class StateManager:
    """Manages robot state transitions with validation"""

    # Define valid state transitions
    VALID_TRANSITIONS = {
        RobotState.IDLE: [RobotState.MOVING, RobotState.ERROR],
        RobotState.MOVING: [RobotState.POSITIONING, RobotState.IDLE, RobotState.ERROR],
        RobotState.POSITIONING: [RobotState.PAINTING, RobotState.MOVING, RobotState.ERROR],
        RobotState.PAINTING: [RobotState.COMPLETED, RobotState.ERROR],
        RobotState.COMPLETED: [RobotState.IDLE, RobotState.ERROR],
        RobotState.ERROR: [RobotState.IDLE]  # Can only recover to IDLE
    }

    def __init__(self, initial_state: RobotState = RobotState.IDLE):
        """
        Initialize State Manager.

        Args:
            initial_state: Starting state (default: IDLE)
        """
        self.current_state = initial_state
        self.previous_state = None
        self.state_enter_time = time.time()
        self.callbacks = []

        logger.info(f"State Manager initialized (state: {initial_state.value})")

    def get_state(self) -> RobotState:
        """
        Get current state.

        Returns:
            Current RobotState
        """
        return self.current_state

    def get_state_duration(self) -> float:
        """
        Get time spent in current state.

        Returns:
            Duration in seconds
        """
        return time.time() - self.state_enter_time

    def set_state(self, new_state: RobotState, force: bool = False) -> bool:
        """
        Transition to new state.

        Args:
            new_state: Target state
            force: Skip validation and force transition

        Returns:
            True if transition successful, False otherwise
        """
        # Check if already in target state
        if self.current_state == new_state:
            logger.debug(f"Already in state: {new_state.value}")
            return True

        # Validate transition (unless forced)
        if not force and not self.can_transition_to(new_state):
            logger.error(f"Invalid transition: {self.current_state.value} → {new_state.value}")
            return False

        # Perform transition
        self.previous_state = self.current_state
        self.current_state = new_state
        self.state_enter_time = time.time()

        logger.info(f"State transition: {self.previous_state.value} → {new_state.value}")

        # Notify callbacks
        for callback in self.callbacks:
            try:
                callback(self.previous_state, new_state)
            except Exception as e:
                logger.error(f"Error in state change callback: {e}")

        return True

    def can_transition_to(self, target_state: RobotState) -> bool:
        """
        Check if transition to target state is valid.

        Args:
            target_state: Desired state

        Returns:
            True if transition is valid
        """
        valid_states = self.VALID_TRANSITIONS.get(self.current_state, [])
        return target_state in valid_states

    def on_state_change(self, callback: Callable):
        """
        Register callback for state changes.

        Args:
            callback: Function(old_state, new_state) to call on transition
        """
        self.callbacks.append(callback)
        logger.debug("State change callback registered")

    def is_idle(self) -> bool:
        """Check if robot is idle"""
        return self.current_state == RobotState.IDLE

    def is_busy(self) -> bool:
        """Check if robot is busy (not idle or error)"""
        return self.current_state not in [RobotState.IDLE, RobotState.ERROR]

    def is_error(self) -> bool:
        """Check if robot is in error state"""
        return self.current_state == RobotState.ERROR

    def reset_to_idle(self) -> bool:
        """
        Force reset to IDLE state.

        Returns:
            True if successful
        """
        logger.info("Forcing reset to IDLE state")
        return self.set_state(RobotState.IDLE, force=True)

    def emergency_stop(self) -> bool:
        """
        Emergency transition to ERROR state.

        Returns:
            True if successful
        """
        logger.warning("EMERGENCY STOP - Transitioning to ERROR state")
        return self.set_state(RobotState.ERROR, force=True)

    def get_state_name(self) -> str:
        """
        Get current state as string.

        Returns:
            State name
        """
        return self.current_state.value

    def get_previous_state(self) -> Optional[RobotState]:
        """
        Get previous state.

        Returns:
            Previous RobotState or None
        """
        return self.previous_state
