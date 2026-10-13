# Short write-up for researchers

[coda-order.pdf](coda-order.pdf) is a four-page note written for readers who work on
animal communication. It states the question, the data and their limits, the
method, the results and the open questions, with references.

The source is [coda-order.html](coda-order.html). `figure1.png` is written by
`python -m coda_recovery.ordering_checks`. To rebuild the PDF with Chromium or
Chrome:

```bash
cd paper
chromium --headless --no-pdf-header-footer --print-to-pdf=coda-order.pdf coda-order.html
```

Every number in the note comes from the tables in [`results/`](../results).
