from uuid import UUID

from sqlalchemy import select # The SQLAlchemy function used to execute ORM query.
from sqlalchemy.ext.asyncio import AsyncSession # Asynchronous session

from .models import User, UserOAuthToken
from .schemas import UserResponse

class UserStore:
    def __init__(self, session: AsyncSession): # Use asynchronous session
        self.session = session

    async def authenticate(self, email: str) -> UserResponse | None:
        # Use the session to execute the ORM query
        result = await self.session.execute( # The execute method (of the session) executes an SQL Query.
            select(User).where(User.email == email)
        ) # Now, this will have a whole Result object, consisting of rows and columns.

        """ Execute returns a Result object, which will have the columns of whatever we have put into 'select'.
        In this case, we've put the whole User object, so it will have only one column, which is the object itself. """

        return result.scalar_one_or_none() # Either zero row (value), or just one; return None or the one object, and raise exception if there are more rows.

        # The 'scalar' method, another method, returns the first column of the first row.

        """ The 'text' function represents the string as a proper SQL query instead of a mere string:
            from sqlalchemy import text

            result = db.execute(text('SELECT version()')) """

    async def create(self, email: str, password_hash: str) -> User:
        # AsyncSession.add() expects an SQLAlchemy ORM instance; we cannot directly insert the UserCreate object into the add method. So:
        user_orm = User(
            email=email,
            password_hash=password_hash
        )

        self.session.add(user_orm) # Put the ORM object into the session, marking it for insertion

        # The 'add' method need not to be awaited because it's not I/O operation, but an in-memeory state manipulation operation.

        await self.session.commit() # Commit the transaction, so the INSERT actually gets persisted
        await self.session.refresh(user_orm) # Reload the object from the database, useful for getting database-generated values/defaults

        # The refresh method receives an SQLAlchemy instance, but it returns 'None'; instead it modifies the connected object in memory.

        return user_orm

    async def get_oauth_token(self, user_id: UUID, provider: str) -> UserOAuthToken | None:
        result = await self.session.execute(
            select(UserOAuthToken).where(
                UserOAuthToken.user_id == user_id,
                UserOAuthToken.provider == provider
            )
        )
        return result.scalar_one_or_none()
