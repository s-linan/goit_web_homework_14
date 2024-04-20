import unittest
from unittest.mock import MagicMock, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdate
from src.repository.contacts import create_contact, get_all_contacts, get_contact, get_contacts, get_contacts_with_birthdays, update_contact, delete_contact, search_contacts_by

class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        # self.user = User(id=1, username='test_user', email='test@ex.ua', password='qwerty', confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_all_contacts(self):
        limit = 10
        offset = 0
        contacts = [Contact(id=1, first_name='test_first_name_1', last_name='test_last_name_1', email='test1@ex.ua'),
                    Contact(id=2, first_name='test_first_name_2', last_name='test_last_name_2', email='test2@ex.ua')]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_all_contacts(limit, offset, self.session)
        self.assertEquals(result, contacts)