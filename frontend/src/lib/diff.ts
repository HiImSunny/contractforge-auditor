// Word-level diff utility for recommendations display (Req 3.6)

export type DiffToken = { text: string; type: "equal" | "added" | "removed" };

export function wordDiff(a: string, b: string): { original: DiffToken[]; proposed: DiffToken[] } {
  const aWords = a.split(/(\s+)/);
  const bWords = b.split(/(\s+)/);

  // Simple LCS-based word diff
  const m = aWords.length;
  const n = bWords.length;

  // Build LCS table
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array(n + 1).fill(0));
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = aWords[i - 1] === bWords[j - 1] ? dp[i - 1][j - 1] + 1 : Math.max(dp[i - 1][j], dp[i][j - 1]);
    }
  }

  // Backtrack
  const original: DiffToken[] = [];
  const proposed: DiffToken[] = [];
  let i = m, j = n;
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && aWords[i - 1] === bWords[j - 1]) {
      original.unshift({ text: aWords[i - 1], type: "equal" });
      proposed.unshift({ text: bWords[j - 1], type: "equal" });
      i--; j--;
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      proposed.unshift({ text: bWords[j - 1], type: "added" });
      j--;
    } else {
      original.unshift({ text: aWords[i - 1], type: "removed" });
      i--;
    }
  }

  return { original, proposed };
}
