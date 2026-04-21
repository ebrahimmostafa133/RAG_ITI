import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';
import { ChatOpenAI } from '@langchain/openai';
import { ChatPromptTemplate, MessagesPlaceholder } from '@langchain/core/prompts';
import { RunnableSequence } from '@langchain/core/runnables';
import { StringOutputParser } from '@langchain/core/output_parsers';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const port = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, './'))); 

// In-memory history (simplified for LCEL)
const sessions = new Map();

app.post('/api/chat', async (req, res) => {
    try {
        const { input, sessionId, config } = req.body;
        
        if (!process.env.OPENAI_API_KEY) {
            return res.status(500).json({ error: 'OpenAI API Key not configured on server.' });
        }

        if (!sessions.has(sessionId)) {
            sessions.set(sessionId, []);
        }

        const history = sessions.get(sessionId);

        const model = new ChatOpenAI({
            openAIApiKey: process.env.OPENAI_API_KEY,
            modelName: config.model || "gpt-4o-mini",
            temperature: config.temperature || 0.7,
        });

        const prompt = ChatPromptTemplate.fromMessages([
            ["system", `You are a world-class Executive Chef 👨‍🍳. 
            Goal: Guide user step-by-step to a meal decision.
            Rules:
            1. Professional, passionate, and encouraging.
            2. NEVER skip steps. Guide sequentially.
            3. Depth: ${config.depth === 'concise' ? 'Snappy kitchen orders' : 'Detailed masterclass'}
            4. Flavor: ${config.temperature > 0.7 ? 'Avant-garde' : 'Classical'}
            5. Technique: Confirm every step before moving forward.`],
            new MessagesPlaceholder("chat_history"),
            ["human", "{input}"],
        ]);

        const chain = RunnableSequence.from([
            prompt,
            model,
            new StringOutputParser(),
        ]);

        const reply = await chain.invoke({
            input: input,
            chat_history: history,
        });

        // Update history
        history.push(["human", input]);
        history.push(["assistant", reply]);
        if (history.length > 20) history.splice(0, 2);

        res.json({ reply });
    } catch (error) {
        console.error('Kitchen Error:', error);
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/clear', (req, res) => {
    const { sessionId } = req.body;
    sessions.delete(sessionId);
    res.json({ message: 'Kitchen cleared.' });
});

app.listen(port, () => {
    console.log(`Gourmet AI Server running at http://localhost:${port}`);
});
