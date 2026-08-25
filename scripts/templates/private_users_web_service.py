from HELPERS.private_users import collect_allowed_user_ids, normalize_user_id


class PrivateUsersWebService:
    def __init__(self, store, admin_ids, static_user_ids):
        self.store = store
        self.admin_ids = collect_allowed_user_ids(admin_ids, [], [])
        self.static_user_ids = collect_allowed_user_ids([], static_user_ids, [])

    @property
    def actor_id(self):
        if not self.admin_ids:
            raise ValueError("At least one Telegram administrator is required")
        return min(self.admin_ids)

    def _is_protected_from_removal(self, user_id):
        return user_id in self.admin_ids or user_id in self.static_user_ids

    @staticmethod
    def _entry(user_id, metadata=None, source=None):
        entry = {"user_id": user_id}
        if source:
            entry["source"] = source
        if isinstance(metadata, dict):
            entry.update(metadata)
        return entry

    def snapshot(self):
        dynamic = self.store.list_entries()
        pending = self.store.list_pending_requests()
        blacklisted = self.store.list_blacklisted()
        active_static_ids = self.static_user_ids - set(blacklisted)
        return {
            "counts": {
                "admins": len(self.admin_ids),
                "static": len(active_static_ids),
                "allowed": len(dynamic),
                "pending": len(pending),
                "blacklisted": len(blacklisted),
            },
            "admins": [
                self._entry(user_id, source="admin")
                for user_id in sorted(self.admin_ids)
            ],
            "static_users": [
                self._entry(user_id, source="config")
                for user_id in sorted(active_static_ids)
            ],
            "allowed_users": [
                self._entry(user_id, dynamic[user_id], "dynamic")
                for user_id in sorted(dynamic)
            ],
            "pending_requests": [
                self._entry(user_id, pending[user_id], "request")
                for user_id in sorted(pending)
            ],
            "blacklisted_users": [
                self._entry(user_id, blacklisted[user_id], "blacklist")
                for user_id in sorted(blacklisted)
            ],
        }

    def add(self, user_id):
        user_id = normalize_user_id(user_id)
        if user_id in self.admin_ids or user_id in self.static_user_ids:
            return "already_allowed"
        if self.store.is_blacklisted(user_id):
            return "blacklisted"
        return "added" if self.store.add(user_id, self.actor_id) else "already_allowed"

    def remove(self, user_id):
        user_id = normalize_user_id(user_id)
        if self._is_protected_from_removal(user_id):
            return "protected"
        return "removed" if self.store.remove(user_id) else "not_dynamic"

    def approve(self, user_id):
        user_id = normalize_user_id(user_id)
        if self._is_protected_from_removal(user_id):
            return "already_allowed"
        return "approved" if self.store.approve(user_id, self.actor_id) else "not_pending"

    def reject(self, user_id):
        user_id = normalize_user_id(user_id)
        if self._is_protected_from_removal(user_id):
            return "protected"
        return "rejected" if self.store.reject(user_id, self.actor_id) else "not_pending"

    def blacklist(self, user_id, reason=None):
        user_id = normalize_user_id(user_id)
        if user_id in self.admin_ids:
            return "protected"
        clean_reason = str(reason or "web_admin").replace("\n", " ").strip()
        if len(clean_reason) > 200:
            raise ValueError("Blacklist reason must be 200 characters or fewer")
        return (
            "blacklisted"
            if self.store.blacklist(user_id, self.actor_id, clean_reason)
            else "already_blacklisted"
        )

    def unblacklist(self, user_id):
        user_id = normalize_user_id(user_id)
        return "unblacklisted" if self.store.unblacklist(user_id) else "not_blacklisted"
