from agent import run_search_agent, run_base_agent
import json
import os

def run_generation():
    # Ensure results directory exists
    folder = "results/results_4th_run"
    os.makedirs(folder, exist_ok=True)

    # 1. Setup Input/Output Paths
    #"data/nq_test_100.jsonl"
    input_path = "group-project/data/nq_test_100.jsonl"

    output_path_nosearch = os.path.join(folder, "predictions_nosearch.jsonl")
    output_path_search = os.path.join(folder, "predictions_search.jsonl")
    output_path_trajectories = os.path.join(folder, "agent_trajectories.jsonl")

    print("Starting Evaluation...")
    #print("Using even smaller dataset selection for testing right now!")

    with open(input_path, 'r') as f_in, \
         open(output_path_nosearch, 'w') as f_nosearch, \
         open(output_path_search, 'w') as f_search, \
         open(output_path_trajectories, 'w') as f_traj:

        count = 0
        # Process each line
        for line in f_in:
            entry = json.loads(line)
            question = entry['question']
            question_id = entry.get('id', None) # Keep ID if available
            answers = entry['answers']
            count += 1
            print(f"\n=== Processing Question {count}, {question[:50]}...     =====")
            
            # Run both agents   
            short_answer, messages, traj_log = run_search_agent(question, max_steps=8)
            base_answer = run_base_agent(question)

            print(f"Search Agent found an Answer: {short_answer}")
            # Save Predictions
            record_search = {"id": question_id,"question": question, "answers": answers, "llm_response": short_answer}
            f_search.write(json.dumps(record_search) + "\n")

            record_nosearch = {"id": question_id,"question": question, "answers": answers, "llm_response": base_answer}
            f_nosearch.write(json.dumps(record_nosearch) + "\n")

            # Save Trajectories
            f_traj.write(json.dumps(traj_log) + "\n")

    print("Generation completed.")

#evaluating script
if __name__ == "__main__":
    run_generation()
