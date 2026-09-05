# Brum — Voice Assistant

Voice-first AI application over a personal/company knowledge base.

**Repo:** https://github.com/pritamexe2k4-cmyk/brum-voice-assistant
**Status:** Phase 1 starting — end-to-end deployed realtime voice + knowledge. Code TBD.

## What Brum is

Brum is a voice assistant people actually talk to. It sits on a knowledge layer (notes, dumps, later Notion / company corpus). Talk in, grounded answers out. Cite what it knows; refuse what it does not.

Longer arc: multi-user company brain-dumps so a team shares one company voice. Phase 1 is the spine — realtime voice + KB for real users.

## Phase 1 (target)

- Browser mic to speech-to-text
- Knowledge store (start: uploads / markdown; Notion later)
- Chat + voice reply: retrieve, then answer with sources or `not_in_knowledge`
- Deployed end-to-end (live URL), not a notebook
- Small real-user set

## Out of Phase 1

- Fine-tuning the base model on dumps
- Full multi-tenant company Brum / lenses
- Notion OAuth (Phase 1.5+)
- Mobile app

## Stack (planned)

Python, FastAPI, LangGraph/RAG retrieval, STT/TTS, simple web client, hosted deploy.

## License

Private build for now — license TBD.