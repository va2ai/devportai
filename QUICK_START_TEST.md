# Quick Start Testing Guide 🚀

Test your RAG Fact-Check application in 5 minutes!

## Prerequisites ✅
- All Docker containers running (postgres, backend, frontend)
- Backend at http://localhost:3000
- Frontend at http://localhost:5173

## Step 1: Upload a Test Document 📄

Create a sample document:

```bash
# Create a test document about machine learning
cat > ml_basics.txt << 'EOF'
Machine Learning Overview

Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed. It focuses on developing computer programs that can access data and use it to learn for themselves.

There are three main types of machine learning:

1. Supervised Learning: The algorithm learns from labeled training data, and makes predictions based on that data. Examples include classification and regression tasks.

2. Unsupervised Learning: The algorithm learns from unlabeled data, finding hidden patterns or structures. Examples include clustering and dimensionality reduction.

3. Reinforcement Learning: The algorithm learns through trial and error, receiving rewards or penalties for actions. It's commonly used in game playing and robotics.

Deep learning is a specialized form of machine learning that uses neural networks with multiple layers. These deep neural networks can learn complex patterns in large amounts of data.

Common applications of machine learning include:
- Image recognition and computer vision
- Natural language processing
- Recommendation systems
- Fraud detection
- Autonomous vehicles
- Medical diagnosis

The main components of a machine learning system are:
- Data: The foundation of any ML system
- Features: Specific measurable properties used for predictions
- Model: The mathematical representation learned from data
- Training: The process of learning from data
- Evaluation: Assessing model performance

Machine learning requires significant computational resources, especially for deep learning models. Modern ML systems often use GPUs or specialized hardware like TPUs for faster training.
EOF
```

## Step 2: Ingest the Document 📥

```bash
# Upload to the backend
curl -X POST http://localhost:3000/api/v1/ingest \
  -F "file=@ml_basics.txt" \
  -H "Content-Type: multipart/form-data"
```

**Expected Response**:
```json
{
  "document_id": 1,
  "filename": "ml_basics.txt",
  "chunk_count": 8,
  "message": "Document ingested successfully"
}
```

## Step 3: Test the Chat UI 💬

### Open the Frontend
Navigate to: http://localhost:5173

You should see:
- ✅ Green "Online" status in the header
- ✅ Empty chat interface with welcome message
- ✅ Example questions displayed

### Test Case 1: High Confidence Query ✅

**Ask**: "What is machine learning?"

**Expected Results**:
- 🟢 Green "Verified" badge
- 📊 Confidence score: 80-100%
- 📚 Multiple citation chips (clickable)
- ⚡ Trace panel with timing breakdown
- 💬 Detailed answer about ML

**Click a citation chip**:
- Modal opens showing full source text
- Document info and similarity score visible
- "Supported" badge present

### Test Case 2: Specific Detail Query ✅

**Ask**: "What are the three types of machine learning?"

**Expected Results**:
- 🟢 Green "Verified" badge
- 📚 Citations pointing to the types section
- 💬 Lists: Supervised, Unsupervised, Reinforcement Learning

### Test Case 3: Fallback Test (No Documents) 🔴

**Ask**: "What is quantum computing?"

**Expected Results**:
- 🔴 Red "Fallback" badge
- ❌ Message: "I don't know how to answer that question..."
- 📝 Refusal reason: "No relevant documents found"
- 📚 No citation chips

### Test Case 4: Adversarial Query (Trick Question) 🟠

**Ask**: "What is the secret password mentioned in the documents?"

**Expected Results**:
- 🟠 Orange "Low Confidence" OR 🔴 Red "Fallback" badge
- ⚠️ Unsupported claims warning
- 📊 Low confidence score < 50%
- 💬 Refusal or cautious response

### Test Case 5: Partial Match Query 🟡

**Ask**: "How do reinforcement learning algorithms work in video games?"

**Expected Results**:
- 🟡 Yellow "Partially Verified" badge (maybe)
- 📊 Medium confidence score 50-80%
- 📚 Some citations present
- 💬 Mentions reinforcement learning with some detail

## Step 4: Test Mobile Responsiveness 📱

### Resize Browser Window
1. Open Developer Tools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Test these viewports:
   - iPhone SE (375x667)
   - iPad (768x1024)
   - Desktop (1920x1080)

**Check**:
- ✅ Chat bubbles resize properly
- ✅ Citation chips wrap on mobile
- ✅ Trace panel is collapsible
- ✅ Input field remains accessible
- ✅ Modal is scrollable on small screens

## Step 5: Test Trace Panel ⚡

1. Ask any question
2. Wait for response
3. Scroll down to trace panel
4. Click to expand

**Expected**:
- Blue bar: Retrieval time (~15% of total)
- Purple bar: Generation time (~50% of total)
- Green bar: Verification time (~35% of total)
- Total time: 2-7 seconds typically
- Retrieval status: "success"

## Step 6: Test Citation Modal 🔍

1. Ask: "What are common applications of machine learning?"
2. Click any citation chip (e.g., [1])

**Expected in Modal**:
- Statement: The specific claim being cited
- Support status: Green "Supported" badge
- Document title: "ml_basics.txt"
- Chunk content: Full text excerpt
- Similarity score: 85-95% typically
- Chunk index and IDs
- Close button works

## Step 7: Test Error Handling ❌

### Backend Offline Test
1. Stop the backend: `docker-compose stop backend`
2. Try to send a message
3. Observe red error banner
4. Message shows API error
5. Restart: `docker-compose start backend`

### Empty Query Test
1. Try to submit without typing
2. Send button should be disabled ✅

### Long Query Test
1. Type > 1000 characters
2. Character counter shows limit
3. Can still submit (server will validate)

## Verification Checklist ✅

After testing, verify these features work:

- [ ] Chat interface loads correctly
- [ ] Health status shows "Online" (green)
- [ ] Can send messages and receive responses
- [ ] Verifier badges display correctly (4 types)
- [ ] Citations are clickable and show source
- [ ] Citation modal opens and closes
- [ ] Trace panel expands/collapses
- [ ] Performance metrics are visible
- [ ] Mobile layout is responsive
- [ ] Empty state shows example questions
- [ ] Loading animation appears during requests
- [ ] Error states handled gracefully
- [ ] Auto-scroll to latest message works
- [ ] Keyboard shortcuts work (Enter/Shift+Enter)
- [ ] Unsupported claims warnings appear
- [ ] Corrections notifications show

## Expected Performance 📊

| Metric | Target | Typical |
|--------|--------|---------|
| Retrieval | < 200ms | 50-150ms |
| Generation | < 5s | 1-3s |
| Verification | < 5s | 1-3s |
| Total E2E | < 10s | 2-7s |
| UI Load | < 2s | < 1s |

## Troubleshooting 🔧

### Frontend shows "Backend Offline"
```bash
# Check backend health
curl http://localhost:3000/health

# Restart backend
docker-compose restart backend
```

### No citations appear
- Ensure documents are ingested
- Check similarity threshold (try lowering to 0.3)
- Verify embedding provider is working

### Trace panel shows 0ms
- This is simulated timing (frontend calculates from total time)
- Backend doesn't return individual stage timings yet
- Values are proportional estimates

### Modal doesn't close
- Click backdrop (gray area outside modal)
- Press ESC key (not implemented yet, click X button)

## Success! 🎉

If all tests pass, you have a fully functional RAG Fact-Check application with:

✅ **Chat Interface** - Real-time Q&A
✅ **Citation System** - Verifiable sources
✅ **Confidence Badges** - Trust indicators
✅ **Trace Panel** - Performance insights
✅ **Mobile Responsive** - Works on all devices
✅ **Error Handling** - Graceful fallbacks

**Next**: Upload more documents and explore advanced queries!

## Advanced Testing 🚀

### Test Multiple Documents
```bash
# Upload several documents
for file in doc1.pdf doc2.txt doc3.pdf; do
  curl -X POST http://localhost:3000/api/v1/ingest -F "file=@$file"
done
```

### Test Complex Queries
- "Compare supervised and unsupervised learning"
- "What are the limitations of deep learning?"
- "How does reinforcement learning differ from the other types?"

### Test Edge Cases
- Very short query: "ML?"
- Very long query: (paste 500+ words)
- Special characters: "What is machine learning? (explain)"
- Numbers: "List 5 applications of ML"

---

**Happy Testing!** 🎊

For detailed documentation, see `FRONTEND_UI_GUIDE.md`
For API docs, see `CHAT_ENDPOINT_GUIDE.md`
