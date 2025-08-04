#!/usr/bin/env python
import os
from customer_finder.crew import CustomerFinder

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

def run():
    """
    Run the research crew.
    """
    inputs = {
        'sector': 'property management',
        'country': 'Switzerland'
    }

    # Create and run the crew
    result = CustomerFinder().crew().kickoff(inputs=inputs)

    # Print the result
    print("\n\n=== FINAL REPORT ===\n\n")
    print(result.raw)

    print("\n\nReport has been saved to output/report.md")

if __name__ == "__main__":
    run()