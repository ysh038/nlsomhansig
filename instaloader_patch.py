"""Instaloader GraphQL doc_id 우회 패치.

Instagram API 변경으로 4.15.1의 doc_id(25980296051578533)가 400을 반환할 때 사용.
https://github.com/instaloader/instaloader/issues/2695
"""

from __future__ import annotations

from instaloader.instaloadercontext import InstaloaderContext

_STALE_DOC_ID = "25980296051578533"
_FIXED_DOC_ID = "27937681195819736"
_EXTRA_VARS = {
    "__relay_internal__pv__PolarisWebSchoolsEnabledrelayprovider": False,
    "enable_integrity_filters": True,
}

_original = InstaloaderContext.doc_id_graphql_query


def _patched_doc_id_graphql_query(self, doc_id, variables, referer=None):
    if doc_id == _STALE_DOC_ID:
        doc_id = _FIXED_DOC_ID
        variables = {**variables, **_EXTRA_VARS}
    return _original(self, doc_id, variables, referer)


def apply() -> None:
    InstaloaderContext.doc_id_graphql_query = _patched_doc_id_graphql_query
