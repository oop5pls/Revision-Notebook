CREATE TABLE files(
full_file_name TEXT PRIMARY KEY
);

CREATE TABLE category(
category_id TEXT PRIMARY KEY,
category_name TEXT UNIQUE
);

CREATE TABLE subject(
subject_id TEXT PRIMARY KEY,
subject TEXT UNIQUE
);

CREATE TABLE terms (
term_id UUID PRIMARY KEY DEFAULT gen_random_uuid(), 
file_of_origin TEXT REFERENCES files(full_file_name),
category_id TEXT REFERENCES category(category_id),
term TEXT UNIQUE,
definition TEXT,
);