create table profiles (
  id uuid references auth.users on delete cascade primary key,
  username text unique,
  role text default 'member' check (role in ('member', 'admin'))
);