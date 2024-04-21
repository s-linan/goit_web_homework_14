import unittest
from unittest.mock import MagicMock, AsyncMock, Mock

from sqlalchemy.ext.asyncio import AsyncSession

from src.entity.models import Contact, User
from src.schemas.contact import ContactSchema, ContactUpdate
from src.repository.contacts import create_contact, get_all_contacts, get_contact, get_contacts, \
     update_contact, delete_contact


class TestAsyncContacts(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.user = User(id=1, username='test_user', email='test@ex.ua', password='qwerty', confirmed=True)
        self.session = AsyncMock(spec=AsyncSession)

    async def test_get_all_contacts(self):
        print(' test_1')
        limit = 10
        offset = 0
        contacts = [Contact(id=1, first_name='test_first_name_1', last_name='test_last_name_1', email='test1@ex.ua',
                            user=self.user),
                    Contact(id=2, first_name='test_first_name_2', last_name='test_last_name_2', email='test2@ex.ua',
                            user=self.user)]
        mocked_contacts = MagicMock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_all_contacts(limit, offset, self.session)
        self.assertEqual(result, contacts)

    async def test_get_contacts(self):
        print(' test_2')
        limit = 10
        offset = 0
        contacts = [Contact(id=1, first_name='test_first_name_1', last_name='test_last_name_1', email='test1@ex.ua',
                            user=self.user),
                    Contact(id=2, first_name='test_first_name_2', last_name='test_last_name_2', email='test2@ex.ua',
                            user=self.user)]
        mocked_contacts = Mock()
        mocked_contacts.scalars.return_value.all.return_value = contacts
        self.session.execute.return_value = mocked_contacts
        result = await get_contacts(limit, offset, self.session, self.user)
        self.assertEqual(result, contacts)

    async def test_create_contact(self):
        print(' test_3')
        body = ContactSchema(first_name='test_first_name_1', last_name='test_last_name_1', email='test1@ex.ua')
        result = await create_contact(body, self.session, self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)

    async def test_update_contact(self):
        print(' test_4')
        body = ContactUpdate(first_name='test_first_name_1', last_name='test_last_name_1', email='test1@ex.ua')
        mocked_contacts = MagicMock()
        mocked_contacts.scalar_one_or_none.return_value = Contact(id=1, first_name='test_first_name_1',
                                                                  last_name='test_last_name_1', email='test1@ex.ua',
                                                                  user=self.user)
        self.session.execute.return_value = mocked_contacts
        result = await update_contact(1, body, self.session, self.user)
        self.assertIsInstance(result, Contact)
        self.assertEqual(result.first_name, body.first_name)
        self.assertEqual(result.last_name, body.last_name)
        self.assertEqual(result.email, body.email)

    async def test_delete_contact(self):
        print(' test_5')
        mocked_contacts = MagicMock()
        mocked_contacts.scalar_one_or_none.return_value = Contact(id=1, first_name='test_first_name_1',
                                                                  last_name='test_last_name_1', email='test1@ex.ua',
                                                                  user=self.user)
        self.session.execute.return_value = mocked_contacts
        result = await delete_contact(1, self.session, self.user)
        self.session.delete.assert_called_once()
        self.session.commit.assert_called_once()
        self.assertIsInstance(result, Contact)

    async def test_get_contact(self):
        print(' test_6')
        mocked_contacts = MagicMock()
        mocked_contacts.scalar_one_or_none.return_value = Contact(id=1, first_name='test_first_name_1',
                                                                  last_name='test_last_name_1', email='test1@ex.ua',
                                                                  user=self.user)
        self.session.execute.return_value = mocked_contacts
        result = await get_contact(1, self.session, self.user)
        self.assertIsInstance(result, Contact)

