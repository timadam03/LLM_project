from agent import run_search_agent, base_agent
import json
import os

def run_evaluation():
    # 1. Setup Input/Output Paths
    input_path = "data/nq_test_100.jsonl"
    output_path_nosearch = "results/predictions_nosearch.jsonl"
    output_path_search = "results/predictions_search.jsonl"
    output_path_trajectories = "results/agent_trajectories.jsonl"
    
    # Ensure results directory exists
    os.makedirs("results", exist_ok=True)

    print("Starting Evaluation...")

    with open(input_path, 'r') as f_in, \
         open(output_path_nosearch, 'w') as f_nosearch, \
         open(output_path_search, 'w') as f_search, \
         open(output_path_trajectories, 'w') as f_traj:

        # Process each line
        for line in f_in:
            entry = json.loads(line)
            question = entry['question']
            question_id = entry.get('id', None) # Keep ID if available
            answers = entry['answers']

            print(f"Processing: {question[:50]}...")
            
            # Run both agents   
            short_answer, detailed_answer, messages = run_search_agent(question)
            base_answer = base_agent(question)

            # Save Predictions
            record_search = {"id": question_id,"question": question, "answers": answers, "llm_response": short_answer}
            f_search.write(json.dumps(record_search) + "\n")

            record_nosearch = {"id": question_id,"question": question, "answers": answers, "llm_response": base_answer}
            f_nosearch.write(json.dumps(record_nosearch) + "\n")

            # Save Trajectories
            record_traj = {"id": question_id,"question": question, "ground_truths": answers, "trajectory": [msg.to_dict() if hasattr(msg, 'to_dict') else msg for msg in messages]}
            f_traj.write(json.dumps(record_traj) + "\n")

    print("Evaluation completed.")

#evaluating script
if __name__ == "__main__":
    run_evaluation()
