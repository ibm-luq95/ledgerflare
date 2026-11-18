"""Test suite verifying target models have been upgraded to encrypted fields and trigram blind index arrays."""

from __future__ import annotations

import pytest
from django.contrib.postgres.fields import ArrayField

from client_account.models import ClientAccount
from core.fields import EncryptedCharField, EncryptedFileField, EncryptedTextField
from discussion.models import Discussion
from important_contact.models import ImportantContact
from job.models import Job
from special_assignment.models import SpecialAssignment
from staff_briefcase.models.accounts import StaffAccounts
from staff_briefcase.models.documents import StaffDocuments
from staff_briefcase.models.notes import StaffNotes


@pytest.mark.unit
def test_client_account_fields_upgraded() -> None:
    """Verify ClientAccount uses EncryptedCharField and EncryptedTextField with trigram blind indexes."""
    user_field = ClientAccount._meta.get_field("account_username")
    assert isinstance(user_field, EncryptedCharField)
    assert getattr(user_field, "trigram_blind_index", False) is True

    url_field = ClientAccount._meta.get_field("account_url")
    assert isinstance(url_field, EncryptedTextField)
    assert getattr(url_field, "trigram_blind_index", False) is True

    user_bidx = ClientAccount._meta.get_field("account_username_bidx")
    assert isinstance(user_bidx, ArrayField)

    url_bidx = ClientAccount._meta.get_field("account_url_bidx")
    assert isinstance(url_bidx, ArrayField)


@pytest.mark.unit
def test_staff_accounts_fields_upgraded() -> None:
    """Verify StaffAccounts uses EncryptedCharField and EncryptedTextField with trigram blind indexes."""
    user_field = StaffAccounts._meta.get_field("username_email")
    assert isinstance(user_field, EncryptedCharField)
    assert getattr(user_field, "trigram_blind_index", False) is True

    url_field = StaffAccounts._meta.get_field("url")
    assert isinstance(url_field, EncryptedTextField)
    assert getattr(url_field, "trigram_blind_index", False) is True

    user_bidx = StaffAccounts._meta.get_field("username_email_bidx")
    assert isinstance(user_bidx, ArrayField)


@pytest.mark.unit
def test_staff_documents_and_notes_upgraded() -> None:
    """Verify StaffDocuments and StaffNotes use EncryptedFileField and EncryptedTextField."""
    file_field = StaffDocuments._meta.get_field("document_file")
    assert isinstance(file_field, EncryptedFileField)

    note_field = StaffNotes._meta.get_field("note")
    assert isinstance(note_field, EncryptedTextField)


@pytest.mark.unit
def test_special_assignment_and_discussion_upgraded() -> None:
    """Verify SpecialAssignment and Discussion attachments and bodies use encrypted fields."""
    sa_file = SpecialAssignment._meta.get_field("attachment")
    assert isinstance(sa_file, EncryptedFileField)
    sa_body = SpecialAssignment._meta.get_field("body")
    assert isinstance(sa_body, EncryptedTextField)
    sa_notes = SpecialAssignment._meta.get_field("notes")
    assert isinstance(sa_notes, EncryptedTextField)

    disc_file = Discussion._meta.get_field("attachment")
    assert isinstance(disc_file, EncryptedFileField)
    disc_body = Discussion._meta.get_field("body")
    assert isinstance(disc_body, EncryptedTextField)


@pytest.mark.unit
def test_important_contact_and_job_notes_upgraded() -> None:
    """Verify ImportantContact notes and Job notes use EncryptedTextField."""
    contact_notes = ImportantContact._meta.get_field("contact_notes")
    assert isinstance(contact_notes, EncryptedTextField)

    job_note = Job._meta.get_field("note")
    assert isinstance(job_note, EncryptedTextField)
