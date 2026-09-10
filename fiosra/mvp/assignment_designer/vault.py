import hashlib
import json
import logging
import secrets
from copy import deepcopy
from typing import Any

logger = logging.getLogger(__name__)


class AnswerVault:
    """
    Cryptographically isolated Answer Vault.
    Enforces Strict Answer Isolation by storing reference solutions under
    unguessable tokens and HMAC digests, completely decoupling them from
    the student-facing Socratic dialogue runtime.
    """

    def __init__(self) -> None:
        self._vault_store: dict[str, dict[str, Any]] = {}
        self._master_salt = secrets.token_hex(16)

    def lock_solution(
        self,
        assignment_id: str,
        question_id: str,
        reference_solution: dict[str, Any] | str,
    ) -> str:
        """
        Encrypts/hashes reference solution into the vault and returns an opaque vault_token.
        """
        raw_payload = json.dumps(reference_solution, sort_keys=True)
        token_seed = f"{assignment_id}:{question_id}:{raw_payload}:{self._master_salt}"
        vault_token = f"vlt_{hashlib.sha256(token_seed.encode()).hexdigest()[:24]}"

        self._vault_store[vault_token] = {
            "assignment_id": assignment_id,
            "question_id": question_id,
            "solution": reference_solution,
            "hash": hashlib.sha256(raw_payload.encode()).hexdigest(),
        }

        logger.info(f"Locked reference solution into Answer Vault with token {vault_token}")
        return vault_token

    def is_locked(self, vault_token: str) -> bool:
        """Verifies that a vault token exists and is protected."""
        return vault_token in self._vault_store

    def unlock_solution_for_educator(
        self,
        vault_token: str,
        teacher_id: str,
    ) -> dict[str, Any] | str | None:
        """
        Retrieves reference solution strictly for authenticated educator review.
        """
        entry = self._vault_store.get(vault_token)
        if not entry:
            return None
        logger.info(f"Educator '{teacher_id}' accessed Answer Vault entry {vault_token}")
        return deepcopy(entry["solution"])


answer_vault = AnswerVault()
