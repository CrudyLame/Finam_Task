Conversation refactoring:

conversation должны содержать блоки (как в текущем парсере), но хранить их поодельности, а не в full_textе

ConvBlock:
- type (user_message, agent_message, system_message)
- text
- agent_type

type - enum:
SYSTEM
USER
AGENT

if block has block_type:
request - USER
response - SYSTEM
intermidiat_response - AGENT

ConvBlock text:
- if type is USER, then full text of block_data
- if type AGENT or SYSTEM, then first 150 chars of block_data

Agent names:
- Supervisor
- Facts assistant
- Questions assistant  
- Departments assistant
- Products assistant
- Tasks assistant
- Meetings assistant
- HR assistant
- FAQ assistant
- Feedback assistant
- Sources assistant
- Statistic assistant
- Designer assistant

Agent types (enum):
- FACTS
- QUESTIONS
- DEPARTMENTS  
- PRODUCTS
- TASKS
- MEETINGS
- HR
- FAQ
- FEEDBACK
- SOURCES
- STATISTIC
- DESIGNER


so if ConvBlock - AGENT block, then extract from block_data agent_type and add it to agent_type field (do search block_data by agent_names)

the Conversation should have new method that return only USER messages, like full_text from all USER blocks in conversation
also Conversation have new field to list of all agent_types in conversation

the Conversation have new method that return user first message (his request) and all agents messages in conversation in text

----------
Update groq_mapper, it should work with new Conversation structure, and work as now, but use in prompts only user messages (that returned by new method) instead of full_text