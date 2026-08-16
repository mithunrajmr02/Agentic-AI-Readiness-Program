import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from phase3.agent.agent import run_agent

def main():
    print("==================================================")
    print("🤖 Inventory Management ReAct Agent (Phase 3)")
    print("Type 'exit' or 'quit' to stop.")
    print("==================================================\n")
    
    while True:
        try:
            query = input("\nUser Query> ")
            if query.strip().lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            if not query.strip():
                continue
                
            print("\nThinking...")
            response = run_agent(query)
            print("\n🤖 Agent Response:\n" + "="*40)
            print(response)
            print("="*40)
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
