--
-- PostgreSQL database dump
--

-- Dumped from database version 16.4
-- Dumped by pg_dump version 16.4

-- Started on 2024-10-17 10:30:02

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 849 (class 1247 OID 24923)
-- Name: conflict_type; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.conflict_type AS ENUM (
    'override',
    'merge',
    'create'
);


ALTER TYPE public.conflict_type OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 216 (class 1259 OID 24793)
-- Name: databases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.databases (
    id integer NOT NULL,
    name text NOT NULL,
    connection_string text NOT NULL
);


ALTER TABLE public.databases OWNER TO postgres;

--
-- TOC entry 215 (class 1259 OID 24792)
-- Name: databases_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.databases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.databases_id_seq OWNER TO postgres;

--
-- TOC entry 4855 (class 0 OID 0)
-- Dependencies: 215
-- Name: databases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.databases_id_seq OWNED BY public.databases.id;


--
-- TOC entry 218 (class 1259 OID 24812)
-- Name: template; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.template (
    id integer NOT NULL,
    table_names character varying(255)[],
    database_name character varying(255),
    database_id integer,
    callbackurl text,
    conflict_type public.conflict_type[]
);


ALTER TABLE public.template OWNER TO postgres;

--
-- TOC entry 217 (class 1259 OID 24811)
-- Name: templates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.templates_id_seq OWNER TO postgres;

--
-- TOC entry 4856 (class 0 OID 0)
-- Dependencies: 217
-- Name: templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.templates_id_seq OWNED BY public.template.id;


--
-- TOC entry 4696 (class 2604 OID 24796)
-- Name: databases id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.databases ALTER COLUMN id SET DEFAULT nextval('public.databases_id_seq'::regclass);


--
-- TOC entry 4697 (class 2604 OID 24815)
-- Name: template id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.template ALTER COLUMN id SET DEFAULT nextval('public.templates_id_seq'::regclass);


--
-- TOC entry 4847 (class 0 OID 24793)
-- Dependencies: 216
-- Data for Name: databases; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.databases (id, name, connection_string) FROM stdin;
1	Testing Excel First	postgresql://postgres:postgres@localhost:5432/testingexcel
2	Testing Excel Second	postgresql://postgres:postgres@localhost:5432/testingexcel2
3	Testing Excel Third	postgresql://postgres:postgres@localhost:5432/testingexcel3
\.


--
-- TOC entry 4849 (class 0 OID 24812)
-- Dependencies: 218
-- Data for Name: template; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.template (id, table_names, database_name, database_id, callbackurl, conflict_type) FROM stdin;
2	{work1}	Testing Excel Second	2	\N	{merge}
3	{table_one}	Testing Excel Third	3	\N	{create}
1	{maluma_question.table_two}	Testing Excel First	1	\N	{override}
\.


--
-- TOC entry 4857 (class 0 OID 0)
-- Dependencies: 215
-- Name: databases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.databases_id_seq', 3, true);


--
-- TOC entry 4858 (class 0 OID 0)
-- Dependencies: 217
-- Name: templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.templates_id_seq', 3, true);


--
-- TOC entry 4699 (class 2606 OID 24800)
-- Name: databases databases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.databases
    ADD CONSTRAINT databases_pkey PRIMARY KEY (id);


--
-- TOC entry 4701 (class 2606 OID 24819)
-- Name: template templates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.template
    ADD CONSTRAINT templates_pkey PRIMARY KEY (id);


--
-- TOC entry 4702 (class 2606 OID 24820)
-- Name: template templates_database_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.template
    ADD CONSTRAINT templates_database_id_fkey FOREIGN KEY (database_id) REFERENCES public.databases(id);


-- Completed on 2024-10-17 10:30:03

--
-- PostgreSQL database dump complete
--

