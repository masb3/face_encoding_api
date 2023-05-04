CREATE TABLE face_encodings (
    id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
    status VARCHAR(20) NOT NULL,
    face_encoding FLOAT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL
);