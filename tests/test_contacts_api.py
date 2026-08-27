import pytest


BASE = "/api/v1/contacts"
PHOTO_JPEG = "data:image/jpeg;base64,/9j/4AAQ"
PHOTO_PNG = "data:image/png;base64,iVBORw0KGgo="


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["database"] == "sqlite"


def test_create_contact(client, payload):
    response = client.post(BASE, json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["email"] == "ada@example.com"
    assert body["full_name"] == "Ada Lovelace"
    assert body["photo"] is None
    assert body["created_at"] and body["updated_at"]


def test_create_and_get_contact_with_photo(client, payload):
    response = client.post(BASE, json={**payload, "photo": PHOTO_JPEG})
    assert response.status_code == 201
    contact_id = response.json()["id"]
    assert response.json()["photo"] == PHOTO_JPEG

    fetched = client.get(f"{BASE}/{contact_id}")
    assert fetched.status_code == 200
    assert fetched.json()["photo"] == PHOTO_JPEG


def test_create_accepts_png_photo(client, payload):
    response = client.post(BASE, json={**payload, "photo": PHOTO_PNG})
    assert response.status_code == 201
    assert response.json()["photo"] == PHOTO_PNG


@pytest.mark.parametrize(
    "photo",
    [
        "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP",
        "data:image/jpeg;base64,not-base64",
        "https://example.com/photo.jpg",
        "data:image/jpeg;base64,",
    ],
)
def test_create_rejects_invalid_photo(client, payload, photo):
    response = client.post(BASE, json={**payload, "photo": photo})
    assert response.status_code == 422


def test_create_rejects_oversized_photo(client, payload):
    import base64

    encoded = base64.b64encode(b"x" * (2 * 1024 * 1024 + 1)).decode()
    response = client.post(BASE, json={**payload, "photo": f"data:image/webp;base64,{encoded}"})
    assert response.status_code == 422


def test_create_requires_valid_email(client, payload):
    response = client.post(BASE, json={**payload, "email": "not-an-email"})
    assert response.status_code == 422


def test_create_requires_names(client, payload):
    response = client.post(BASE, json={**payload, "first_name": ""})
    assert response.status_code == 422


def test_duplicate_email_conflicts(client, payload):
    assert client.post(BASE, json=payload).status_code == 201
    response = client.post(BASE, json={**payload, "email": "ADA@example.com"})
    assert response.status_code == 409


def test_get_contact(client, payload):
    contact_id = client.post(BASE, json=payload).json()["id"]
    response = client.get(f"{BASE}/{contact_id}")
    assert response.status_code == 200
    assert response.json()["id"] == contact_id


def test_get_missing_contact_returns_404(client):
    assert client.get(f"{BASE}/9999").status_code == 404


def test_list_pagination_and_total(client, payload):
    for index in range(5):
        client.post(BASE, json={**payload, "email": f"user{index}@example.com"})

    response = client.get(BASE, params={"limit": 2, "offset": 2})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 5
    assert len(body["items"]) == 2
    assert body["limit"] == 2 and body["offset"] == 2


def test_list_search(client, payload):
    client.post(BASE, json=payload)
    client.post(
        BASE,
        json={**payload, "first_name": "Grace", "last_name": "Hopper", "email": "grace@example.com", "company": "US Navy"},
    )

    hits = client.get(BASE, params={"search": "hopper"}).json()
    assert hits["total"] == 1
    assert hits["items"][0]["last_name"] == "Hopper"

    by_company = client.get(BASE, params={"search": "navy"}).json()
    assert by_company["total"] == 1

    misses = client.get(BASE, params={"search": "nobody"}).json()
    assert misses["total"] == 0


def test_list_sorting(client, payload):
    client.post(BASE, json={**payload, "last_name": "Zhang", "email": "z@example.com"})
    client.post(BASE, json={**payload, "last_name": "Adams", "email": "a@example.com"})

    names = [
        item["last_name"]
        for item in client.get(BASE, params={"sort_by": "last_name", "order": "asc"}).json()["items"]
    ]
    assert names == ["Adams", "Zhang"]


def test_list_rejects_bad_sort_field(client):
    assert client.get(BASE, params={"sort_by": "; DROP TABLE contacts"}).status_code == 422


def test_patch_updates_only_sent_fields(client, payload):
    contact_id = client.post(BASE, json=payload).json()["id"]
    response = client.patch(f"{BASE}/{contact_id}", json={"phone": "+1-000-000-0000"})
    assert response.status_code == 200
    body = response.json()
    assert body["phone"] == "+1-000-000-0000"
    assert body["first_name"] == "Ada"
    assert body["company"] == "Analytical Engines"


def test_patch_without_photo_preserves_photo(client, payload):
    contact_id = client.post(BASE, json={**payload, "photo": PHOTO_JPEG}).json()["id"]

    response = client.patch(f"{BASE}/{contact_id}", json={"phone": "+1-000-000-0000"})

    assert response.status_code == 200
    assert response.json()["photo"] == PHOTO_JPEG


def test_patch_can_replace_photo(client, payload):
    contact_id = client.post(BASE, json={**payload, "photo": PHOTO_JPEG}).json()["id"]

    response = client.patch(f"{BASE}/{contact_id}", json={"photo": PHOTO_PNG})

    assert response.status_code == 200
    assert response.json()["photo"] == PHOTO_PNG

    removed = client.patch(f"{BASE}/{contact_id}", json={"photo": None})
    assert removed.status_code == 200
    assert removed.json()["photo"] is None


def test_put_preserves_submitted_photo_and_can_remove_it(client, payload):
    contact_id = client.post(BASE, json={**payload, "photo": PHOTO_JPEG}).json()["id"]
    replacement = {**payload, "company": "Updated Company", "photo": PHOTO_JPEG}

    updated = client.put(f"{BASE}/{contact_id}", json=replacement)
    assert updated.status_code == 200
    assert updated.json()["photo"] == PHOTO_JPEG

    removed = client.put(f"{BASE}/{contact_id}", json={**payload, "photo": None})
    assert removed.status_code == 200
    assert removed.json()["photo"] is None


def test_patch_duplicate_email_conflicts(client, payload):
    first = client.post(BASE, json=payload).json()["id"]
    client.post(BASE, json={**payload, "email": "grace@example.com"})
    response = client.patch(f"{BASE}/{first}", json={"email": "grace@example.com"})
    assert response.status_code == 409


def test_patch_same_email_is_allowed(client, payload):
    contact_id = client.post(BASE, json=payload).json()["id"]
    response = client.patch(f"{BASE}/{contact_id}", json={"email": payload["email"]})
    assert response.status_code == 200


def test_put_replaces_contact(client, payload):
    contact_id = client.post(BASE, json=payload).json()["id"]
    response = client.put(
        f"{BASE}/{contact_id}",
        json={"first_name": "Grace", "last_name": "Hopper", "email": "grace@example.com"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Grace Hopper"
    assert body["company"] is None  # omitted fields are cleared by PUT


def test_put_missing_contact_returns_404(client):
    response = client.put(
        f"{BASE}/9999",
        json={"first_name": "A", "last_name": "B", "email": "ab@example.com"},
    )
    assert response.status_code == 404


def test_delete_contact(client, payload):
    contact_id = client.post(BASE, json=payload).json()["id"]
    assert client.delete(f"{BASE}/{contact_id}").status_code == 204
    assert client.get(f"{BASE}/{contact_id}").status_code == 404
    assert client.delete(f"{BASE}/{contact_id}").status_code == 404


def test_root_lists_entrypoints(client):
    body = client.get("/").json()
    assert body["contacts"] == BASE
