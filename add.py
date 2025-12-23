# update_roles.py
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://tcxii_user:w9OQanO9T1N8Sa5sEPpKS93rElXMb98y@dpg-d54splshg0os739o11p0-a.virginia-postgres.render.com/tcxii"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Set default role for all agents that have NULL
    conn.execute(text("UPDATE agents SET role = 'admin' WHERE role IS NULL"))
    conn.commit()
    print("✅ All agents now have a role!")

 # we uised this file to update the remote db because we forgot to add a column 'role' when we created the agents table.