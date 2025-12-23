# main.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from db.database import engine, SessionLocal
from api.router import api_router
import db.models as models
from auth.security import verify_token, get_current_admin
import logging
from sqlalchemy import text

#test the api connection to the database
# Logging setup — uvicorn will capture these logs too
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("doxa")

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


# roles
@app.middleware("http")
async def role_middleware(request: Request, call_next):
    path = request.url.path
    logger.info(f"[JWT-MW] {request.method} {path} - checking role")
    print(f"[JWT-MW] {request.method} {path} - checking role")

    # Allow unauthenticated paths: only the login endpoint and docs/openapi
    if (
        path.startswith("/agents/modify/")
        or path.startswith("/agents/add")
        or path.startswith("/agents/delete")
    ):
        try:
            get_current_admin(current_agent=request.state.current_agent)  # will raise if not admin
        except Exception as e:
            logger.warning(f"[JWT-MW] {request.method} {path} - role verification failed: {e}")
            print(f"[JWT-MW] {request.method} {path} - role verification failed: {e}")
            return JSONResponse(status_code=403, content={"detail": "Admin required"})
    else:
        logger.info(f"[JWT-MW] {request.method} {path} - skipped (public)")
        print(f"[JWT-MW] {request.method} {path} - skipped (public)")
    return await call_next(request)



# auth
@app.middleware("http")
async def jwt_auth_middleware(request: Request, call_next):
    path = request.url.path
    logger.info(f"[JWT-MW] {request.method} {path} - checking authentication")
    print(f"[JWT-MW] {request.method} {path} - checking authentication")

    # Allow unauthenticated paths: only the login endpoint and docs/openapi
    if (
        path == "/auth/login"
        or path.startswith("/openapi.json")
        or path.startswith("/docs")
        or path.startswith("/redoc")
    ):
        logger.info(f"[JWT-MW] {request.method} {path} - skipped (public)")
        print(f"[JWT-MW] {request.method} {path} - skipped (public)")
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.info(f"[JWT-MW] {request.method} {path} - no Authorization header")
        print(f"[JWT-MW] {request.method} {path} - no Authorization header")
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid auth scheme")
    except ValueError:
        logger.warning(f"[JWT-MW] {request.method} {path} - invalid Authorization header")
        print(f"[JWT-MW] {request.method} {path} - invalid Authorization header")
        return JSONResponse(status_code=401, content={"detail": "Invalid Authorization header"})

    db = SessionLocal()
    try:
        agent = verify_token(token, db)
        # attach authenticated agent to request.state for handlers to use
        request.state.current_agent = agent
        logger.info(f"[JWT-MW] {request.method} {path} - token verified for agent_id={agent.id}")
        print(f"[JWT-MW] {request.method} {path} - token verified for agent_id={agent.id}")
    except Exception as e:
        db.close()
        logger.warning(f"[JWT-MW] {request.method} {path} - token verification failed: {e}")
        print(f"[JWT-MW] {request.method} {path} - token verification failed: {e}")
        if hasattr(e, "status_code"):
            return JSONResponse(status_code=e.status_code, content={"detail": getattr(e, "detail", "Not authenticated")})
        return JSONResponse(status_code=401, content={"detail": "Invalid token"})
    finally:
        db.close()

    try:
        response = await call_next(request)
    except Exception as e:
        logger.exception(f"[JWT-MW] {request.method} {path} - exception during request: {e}")
        print(f"[JWT-MW] {request.method} {path} - exception during request: {e}")
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})

    status = response.status_code
    agent_info = getattr(getattr(request, "state", None), "current_agent", None)
    agent_id = getattr(agent_info, "id", None)

    if status < 400:
        logger.info(f"[JWT-MW] {request.method} {path} - completed {status} - success - agent_id={agent_id}")
        print(f"[JWT-MW] {request.method} {path} - completed {status} - success - agent_id={agent_id}")
    else:
        logger.warning(f"[JWT-MW] {request.method} {path} - completed {status} - failure - agent_id={agent_id}")
        print(f"[JWT-MW] {request.method} {path} - completed {status} - failure - agent_id={agent_id}")

    return response


app.include_router(api_router)


if __name__ == "__main__":
    # Run with: python main.py  (binds to 0.0.0.0)
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=7000, reload=True)


