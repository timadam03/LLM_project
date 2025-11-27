import os
import time
import sys

RESULTS_FILE = "assignment4/results/aime24_results_math.jsonl"
TOTAL_ROLLOUTS = 120  # 30 problems * 4 rollouts

def main():
    if not os.path.exists(RESULTS_FILE):
        print("Results file not found yet.")
        return

    print("Monitoring progress... (Press Ctrl+C to stop)")
    print("-" * 40)
    
    start_time = time.time()
    start_lines = 0
    
    try:
        while True:
            with open(RESULTS_FILE, 'r') as f:
                lines = len(f.readlines())
            
            done = lines
            remaining = TOTAL_ROLLOUTS - done
            percent = (done / TOTAL_ROLLOUTS) * 100
            
            # Simple visual bar
            bar_len = 20
            filled = int(bar_len * (done / TOTAL_ROLLOUTS))
            bar = "█" * filled + "-" * (bar_len - filled)
            
            # Clear line and update
            sys.stdout.write(f"\r[{bar}] {done}/{TOTAL_ROLLOUTS} ({percent:.1f}%) completed")
            sys.stdout.flush()
            
            if done >= TOTAL_ROLLOUTS:
                print("\nDone!")
                break
                
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\nStopped monitoring.")

if __name__ == "__main__":
    main()

