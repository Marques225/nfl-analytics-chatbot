import torch
import torch.nn as nn
import torch.optim as optim
from transformer_model import NFLTransformer
import os

# --- 1. ROBUST PATH SETUP ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(BACKEND_DIR, "data", "qa_dataset.txt")
MODEL_SAVE_PATH = os.path.join(SCRIPT_DIR, "tiny_nfl_transformer.pth")

print(f"📂 Script Location: {SCRIPT_DIR}")
print(f"📂 Looking for Data at: {DATA_PATH}")

# --- 2. Hyperparameters (Updated) ---
D_MODEL = 64
NUM_HEADS = 2
NUM_LAYERS = 2
D_FF = 128
MAX_SEQ_LEN = 64  # <--- INCREASED FROM 32 TO 64 TO PREVENT CRASH
DROPOUT = 0.1
LEARNING_RATE = 0.001
EPOCHS = 100      # <--- INCREASED TO 100 FOR BETTER RESULTS

# --- 3. Load Data & Build Vocabulary ---
if not os.path.exists(DATA_PATH):
    print(f"❌ ERROR: Data file not found at {DATA_PATH}")
    print("   👉 Did you run 'python backend/ml/generate_data.py' first?")
    exit(1)

print("📚 Loading Data...")
with open(DATA_PATH, "r", encoding="utf-8") as f:
    text_data = f.read().splitlines()

chars = sorted(list(set("".join(text_data))))
vocab_size = len(chars) + 2 
char_to_idx = {ch: i+1 for i, ch in enumerate(chars)}
idx_to_char = {i+1: ch for i, ch in enumerate(chars)}
PAD_IDX = 0

print(f"   Vocab Size: {vocab_size} characters")

def encode(text):
    return [char_to_idx.get(c, PAD_IDX) for c in text]

def decode(indices):
    return "".join([idx_to_char.get(i, '') for i in indices])

# --- 4. Prepare Tensors ---
input_data = []
target_data = []

for line in text_data:
    tokenized = encode(line)
    # Truncate to MAX_SEQ_LEN
    if len(tokenized) > MAX_SEQ_LEN:
        tokenized = tokenized[:MAX_SEQ_LEN]
    else:
        tokenized += [PAD_IDX] * (MAX_SEQ_LEN - len(tokenized))
        
    input_data.append(tokenized[:-1]) 
    target_data.append(tokenized[1:]) 

inputs = torch.tensor(input_data, dtype=torch.long)
targets = torch.tensor(target_data, dtype=torch.long)

# --- 5. Initialize Model ---
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Note: We subtract 1 from MAX_SEQ_LEN for the model because inputs are 1 token shorter than sequence
model = NFLTransformer(vocab_size, D_MODEL, NUM_HEADS, NUM_LAYERS, D_FF, MAX_SEQ_LEN-1, DROPOUT).to(device)
criterion = nn.CrossEntropyLoss(ignore_index=PAD_IDX)
optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# --- 6. Training Loop ---
print(f"🚀 Starting Training on {device}...")
model.train()

for epoch in range(EPOCHS):
    inputs, targets = inputs.to(device), targets.to(device)
    
    optimizer.zero_grad()
    output = model(inputs) 
    loss = criterion(output.view(-1, vocab_size), targets.view(-1))
    loss.backward()
    optimizer.step()
    
    if (epoch+1) % 10 == 0:
        print(f"   Epoch {epoch+1}/{EPOCHS} | Loss: {loss.item():.4f}")

# --- 7. Save Model ---
torch.save(model.state_dict(), MODEL_SAVE_PATH)
print(f"💾 Model Saved to: {MODEL_SAVE_PATH}")

# --- 8. Quick Test (Inference) ---
print("\n🤖 TEST INFERENCE (Generation):")
model.eval()
test_str = "Question: Who is"
print(f"   Input: {test_str}")
input_seq = torch.tensor([encode(test_str)], dtype=torch.long).to(device)

generated = input_seq
for _ in range(30): # Generate 30 characters
    with torch.no_grad():
        # SAFETY CROP: Ensure we never feed more than the model's max limit
        context_window = generated[:, -(MAX_SEQ_LEN-1):]
        
        output = model(context_window)
        next_token_logits = output[:, -1, :]
        next_token_id = next_token_logits.argmax(dim=-1).unsqueeze(0)
        generated = torch.cat((generated, next_token_id), dim=1)

result_text = decode(generated[0].tolist())
print(f"   Result: {result_text}")