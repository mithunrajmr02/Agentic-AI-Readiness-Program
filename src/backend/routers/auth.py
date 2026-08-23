import hashlib
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
import structlog

from src.backend.database import get_db
from src.backend.models import User
from src.backend.schemas import UserCreate, UserResponse, Token

logger = structlog.get_logger()

SECRET_KEY = os.getenv("SECRET_KEY", "secret-key-poc-07-inventory-management-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# Roles from overview.md:19-22 -- Store Manager and Warehouse Staff. `manager`
# is the privileged one (PO approval); `staff` is the only role a caller may
# assign to itself at /register.
MANAGER_ROLE = "manager"
SELF_ASSIGNABLE_ROLE = "staff"
VALID_ROLES = {MANAGER_ROLE, SELF_ASSIGNABLE_ROLE}

# The bootstrap manager. Overridable so a deployment is not pinned to a password
# that is written down in this file; the defaults keep local runs working
# unchanged and match what the service clients fall back to.
DEFAULT_ADMIN_EMAIL = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@retail.com")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")

pwd_context = CryptContext(schemes=["pbkdf2_sha256", "bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


class LegacyPasswordHasher:
    @staticmethod
    def verify(plain_password: str, hashed_password: str) -> bool:
        salt = os.getenv("PASSWORD_SALT", SECRET_KEY).encode("utf-8")
        digest = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt, 100_000)
        return digest.hex() == hashed_password



def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        if pwd_context.verify(plain_password, hashed_password):
            return True
    except Exception:
        pass
    return LegacyPasswordHasher.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def ensure_default_user(db: Session) -> User:
    """Provision the bootstrap manager account if it does not exist.

    Called from `main.lifespan` at startup. It used to be reachable *only* from
    the two bypass branches inside `get_current_user`, so deleting those would
    have left a fresh database with no account at all and nothing able to log in
    -- the service clients included. Startup is where this belongs anyway: the
    account should exist because the app booted, not because someone made an
    unauthenticated request.
    """
    user = db.query(User).filter(User.email == DEFAULT_ADMIN_EMAIL).first()
    if not user:
        user = User(
            email=DEFAULT_ADMIN_EMAIL,
            hashed_password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
            full_name="Admin",
            role=MANAGER_ROLE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user



def get_current_user(token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """Resolve the caller from a bearer JWT, or reject the request with 401.

    This used to do the exact inverse of authentication. Two branches stood
    where the rejection belongs:

      * no token at all -> `return ensure_default_user(db)`, which provisioned
        and returned the `manager`-role admin account;
      * the literal string `"test_token"` -> the same admin account.

    So a request carrying *no* credentials was served as a manager, while a
    request carrying a malformed token was correctly refused -- verified against
    the running service: anonymous `GET /api/v1/products` answered 200,
    anonymous `POST /api/v1/suppliers` answered 201 and created a row, and
    `Authorization: Bearer not-a-real-jwt` answered 401. Every one of the twelve
    inventory routes declares `Depends(get_current_user)`, so all twelve were
    open, and `inventory.py` stamps `recorded_by=current_user.full_name` onto
    each StockMovement -- meaning the audit trail that US-07-P1-02 exists to
    provide was attributing every movement in the system to "Admin".

    `oauth2_scheme` is constructed with `auto_error=False`, which is what let a
    tokenless request reach this body at all; the 401 now has to be raised here.
    The `Bearer ` strip below is still required because `test_auth.py` calls this
    function directly with a `"Bearer <jwt>"` string rather than through the
    dependency (FastAPI's own scheme strips the prefix before injection).
    """
    if not token:
        logger.warning(
            "auth_missing_token",
            poc_id="POC-07",
            phase="P1",
            reason="no_credentials_presented",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token.startswith("Bearer "):
        token = token.split(" ", 1)[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except JWTError as exc:
        logger.warning(
            "auth_token_invalid",
            poc_id="POC-07",
            phase="P1",
            error=str(exc),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        # Detail text is asserted verbatim by test_get_current_user_user_not_found.
        logger.warning("auth_subject_unknown", poc_id="POC-07", phase="P1", user_email=email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning("auth_user_inactive", poc_id="POC-07", phase="P1", user_email=email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(
        "token_validated",
        poc_id="POC-07",
        phase="P1",
        user_email=user.email,
        user_role=user.role,
    )
    return user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Optional[User]:
    """Resolve the caller if credentials were supplied, else None -- never raises.

    Used only by `/register`, which has to stay reachable anonymously (that is
    how the first account is created) while still being able to tell whether a
    privileged caller is on the other end.
    """
    if not token:
        return None
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    caller: Optional[User] = Depends(get_optional_user),
):
    """Create an account. Only `staff` may be self-assigned.

    `role=user_data.role or "staff"` took the role straight off the request body,
    so `POST /api/v1/auth/register {"role": "manager"}` -- an endpoint that must
    stay open for the first account to exist -- minted a manager for anybody who
    asked. Verified against the running service: it answered 201 with
    `"role":"manager"` and no credentials. `overview.md:19` reserves PO approval
    for the Store Manager, and the role is signed into the JWT at login, so
    self-assignment forges the claim any future authorization would rely on.

    Refused with 403 rather than quietly downgraded to `staff`: silently handing
    back a different role than the one requested is the kind of surprise that
    gets debugged for an hour, and a caller genuinely provisioning a manager
    needs to know an existing manager's token is the way to do it.
    """
    requested_role = (user_data.role or SELF_ASSIGNABLE_ROLE).strip().lower()

    if requested_role not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{requested_role}'. Valid roles: {', '.join(sorted(VALID_ROLES))}",
        )

    if requested_role != SELF_ASSIGNABLE_ROLE and (caller is None or caller.role != MANAGER_ROLE):
        logger.warning(
            "role_escalation_refused",
            poc_id="POC-07",
            phase="P1",
            requested_role=requested_role,
            requested_for=user_data.email,
            caller=caller.email if caller else "anonymous",
        )
        raise HTTPException(
            status_code=403,
            detail=(
                f"Role '{requested_role}' cannot be self-assigned. "
                f"Only '{SELF_ASSIGNABLE_ROLE}' may be requested without credentials; "
                f"a '{MANAGER_ROLE}' access token is required to create other roles."
            ),
        )

    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed,
        full_name=user_data.full_name,
        role=requested_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logger.info(
        "user_registered",
        poc_id="POC-07",
        phase="P1",
        user_email=user.email,
        user_role=user.role,
        granted_by=caller.email if caller else "self_service",
    )
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        # OBSERVABILITY_GUIDE.md:448 requires login *failure* to be logged, not
        # just success. Only the success path was instrumented, so a password
        # spray left no trace at all. The reason is recorded but the submitted
        # password never is, and the response stays deliberately ambiguous about
        # which half was wrong so the endpoint is not a user-enumeration oracle.
        logger.warning(
            "user_login_failed",
            poc_id="POC-07",
            phase="P1",
            user_email=form_data.username,
            reason="unknown_email" if not user else "bad_password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        logger.warning(
            "user_login_failed",
            poc_id="POC-07",
            phase="P1",
            user_email=form_data.username,
            reason="inactive_account",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": user.email, "role": user.role})
    logger.info(
        "user_login_success", poc_id="POC-07", phase="P1", user_email=user.email, user_role=user.role
    )
    return {"access_token": access_token, "token_type": "bearer"}

