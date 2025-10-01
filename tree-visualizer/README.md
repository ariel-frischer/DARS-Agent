This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the page like this.



## Configuration(.env file)
The app relies on a `.env` file where you can configure the paths for key input files:

```
ROOT_INPUT_FILE: The main .root file that needs to be visualized.

JSON_EVAL_FILE: The final evaluation file generated after running the model, representing the end nodes and whether a node is an accepted or rejected solution

ROOT_INPUT_FOLDER: Contains all 16 possible .root files, each representing different trajectory cases: ["Append", "Create", "Edit", "Submit"].
```

## Features

The Tree Visualizer provides an interactive interface to:
- **Visualize agent trajectories** as tree structures
- **Analyze decision points** where the agent branched to explore different solutions
- **Compare different paths** taken by the agent
- **Identify successful vs. failed solutions** based on evaluation results
- **Examine trajectory patterns** across different action types (Append, Create, Edit, Submit)

This tool is essential for understanding how DARS explores the solution space and makes decisions during the problem-solving process.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

