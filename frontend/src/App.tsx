import styles from "./App.module.css";
import { PipelineRail } from "./components/PipelineRail";
import { DraftScreen } from "./screens/DraftScreen";
import { GuardrailScreen } from "./screens/GuardrailScreen";
import { RequestScreen } from "./screens/RequestScreen";
import { RetrievalScreen } from "./screens/RetrievalScreen";
import { ReviewScreen } from "./screens/ReviewScreen";
import { usePipelineState } from "./state/pipelineState";

function App() {
  const [state, dispatch] = usePipelineState();

  return (
    <div className={styles.layout}>
      <PipelineRail currentStage={state.stage} />
      <main className={styles.main}>
        {state.stage === "request" && <RequestScreen state={state} dispatch={dispatch} />}
        {state.stage === "guardrail" && <GuardrailScreen state={state} dispatch={dispatch} />}
        {state.stage === "retrieval" && <RetrievalScreen state={state} dispatch={dispatch} />}
        {state.stage === "review" && <ReviewScreen state={state} dispatch={dispatch} />}
        {state.stage === "draft" && <DraftScreen state={state} dispatch={dispatch} />}
      </main>
    </div>
  );
}

export default App;
