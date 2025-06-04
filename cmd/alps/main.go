package main

import (
    "encoding/json"
    "errors"
    "flag"
    "fmt"
    "io/ioutil"
    "os"
    "regexp"
    "strings"
    "time"
)

type Task struct {
    ID                string   `json:"id"`
    Name              string   `json:"name"`
    Description       string   `json:"description"`
    AcceptanceCriteria []string `json:"acceptance_criteria"`
    EstimatedHours    int      `json:"estimated_hours"`
    Difficulty        string   `json:"difficulty"`
    Dependencies      []string `json:"dependencies"`
    Priority          int      `json:"priority"`
    Status            string   `json:"status"`
}

type Feature struct {
    ID    string  `json:"id"`
    Name  string  `json:"name"`
    Tasks []Task  `json:"tasks"`
    Raw   string  `json:"-"`
}

type Project struct {
    Name          string    `json:"name"`
    CreatedAt     string    `json:"created_at"`
    TotalFeatures int       `json:"total_features"`
    TotalTasks    int       `json:"total_tasks"`
    EstimatedDays float64   `json:"estimated_days"`
    Features      []Feature `json:"features"`
}

const version = "0.1.0"

func main() {
    if len(os.Args) < 2 {
        usage()
        os.Exit(1)
    }

    switch os.Args[1] {
    case "process":
        processCmd(os.Args[2:])
    case "--help", "-h", "help":
        usage()
    case "--version", "version":
        fmt.Println("alps-breakdown", version)
    default:
        fmt.Println("unknown command:", os.Args[1])
        usage()
        os.Exit(1)
    }
}

func usage() {
    fmt.Println(`alps-breakdown - ALPS Trail CLI

Usage:
  alps-breakdown process <file_path> [options]

Options:
  -o, --output  Output file path (default: tasks.yaml)
  -v, --verbose Enable verbose logging
  -f, --format  Output format: yaml or json (default: yaml)
  --version     Show version information
  -h, --help    Show help`)
}

func processCmd(args []string) {
    fs := flag.NewFlagSet("process", flag.ExitOnError)
    output := fs.String("output", "tasks.yaml", "output file path")
    fs.StringVar(output, "o", "tasks.yaml", "output file path")
    verbose := fs.Bool("verbose", false, "verbose output")
    fs.BoolVar(verbose, "v", false, "verbose output")
    format := fs.String("format", "yaml", "output format")
    fs.StringVar(format, "f", "yaml", "output format")
    fs.Parse(args)

    if fs.NArg() < 1 {
        fmt.Fprintln(os.Stderr, "missing ALPS file path")
        fs.Usage()
        os.Exit(1)
    }
    filePath := fs.Arg(0)

    if *verbose {
        fmt.Println("Processing:", filePath)
        fmt.Println("Extracting Section 6...")
    }

    section, err := extractSection6(filePath)
    if err != nil {
        fmt.Fprintln(os.Stderr, "error:", err)
        os.Exit(1)
    }

    if *verbose {
        fmt.Println("Analyzing features...")
    }

    features := parseFeatures(section)
    tasks := generateTasks(features)

    if *verbose {
        fmt.Println("Generating output...")
    }

    project := Project{
        Name:          "ALPS Project",
        CreatedAt:     time.Now().UTC().Format(time.RFC3339),
        TotalFeatures: len(features),
        TotalTasks:    len(tasks),
        EstimatedDays: 0,
        Features:      features,
    }

    for i := range features {
        features[i].Tasks = []Task{tasks[i]}
    }

    var out string
    if strings.ToLower(*format) == "json" {
        b, _ := json.MarshalIndent(project, "", "  ")
        out = string(b)
    } else {
        out = toYAML(project)
    }

    if err := ioutil.WriteFile(*output, []byte(out), 0644); err != nil {
        fmt.Fprintln(os.Stderr, "failed to write output:", err)
        os.Exit(1)
    }

    fmt.Println("✓ Complete! Output saved to:", *output)
    fmt.Printf("Features processed: %d\n", len(features))
    fmt.Printf("Tasks generated: %d\n", len(tasks))
}

func extractSection6(path string) (string, error) {
    data, err := os.ReadFile(path)
    if err != nil {
        return "", err
    }
    content := string(data)
    lower := strings.ToLower(content)
    re := regexp.MustCompile(`(?m)^## +(?:section|섹션) 6.*$`)
    loc := re.FindStringIndex(lower)
    if loc == nil {
        return "", errors.New("section 6 not found")
    }
    start := loc[0]
    rest := content[start:]
    // find next level 2 heading
    re2 := regexp.MustCompile(`(?m)^## +`)
    loc2 := re2.FindStringIndex(rest[2:])
    end := len(rest)
    if loc2 != nil {
        end = loc2[0] + 2
    }
    section := strings.TrimSpace(rest[:end])
    return section, nil
}

func parseFeatures(section string) []Feature {
    lines := strings.Split(section, "\n")
    var features []Feature
    var current *Feature
    re := regexp.MustCompile(`^### +([0-9]+\.[0-9]+) +(.+)$`)
    for _, line := range lines {
        if m := re.FindStringSubmatch(line); m != nil {
            if current != nil {
                features = append(features, *current)
            }
            id := strings.TrimPrefix(m[1], "6.")
            current = &Feature{ID: "F" + id, Name: strings.TrimSpace(m[2])}
            continue
        }
        if current != nil {
            if current.Raw != "" {
                current.Raw += "\n"
            }
            current.Raw += line
        }
    }
    if current != nil {
        features = append(features, *current)
    }
    return features
}

func generateTasks(features []Feature) []Task {
    tasks := make([]Task, len(features))
    for i, f := range features {
        tid := fmt.Sprintf("T%d.1", i+1)
        tasks[i] = Task{
            ID:          tid,
            Name:        "Implement " + f.Name,
            Description: strings.TrimSpace(f.Raw),
            AcceptanceCriteria: []string{},
            EstimatedHours:    0,
            Difficulty:        "Medium",
            Dependencies:      []string{},
            Priority:          1,
            Status:            "Not Started",
        }
    }
    return tasks
}

func toYAML(p Project) string {
    var b strings.Builder
    b.WriteString("project:\n")
    b.WriteString(fmt.Sprintf("  name: \"%s\"\n", p.Name))
    b.WriteString(fmt.Sprintf("  created_at: \"%s\"\n", p.CreatedAt))
    b.WriteString(fmt.Sprintf("  total_features: %d\n", p.TotalFeatures))
    b.WriteString(fmt.Sprintf("  total_tasks: %d\n", p.TotalTasks))
    b.WriteString(fmt.Sprintf("  estimated_days: %.1f\n\n", p.EstimatedDays))
    b.WriteString("features:\n")
    for _, f := range p.Features {
        b.WriteString(fmt.Sprintf("  - id: \"%s\"\n", f.ID))
        b.WriteString(fmt.Sprintf("    name: \"%s\"\n", escape(f.Name)))
        b.WriteString("    tasks:\n")
        for _, t := range f.Tasks {
            b.WriteString(fmt.Sprintf("      - id: \"%s\"\n", t.ID))
            b.WriteString(fmt.Sprintf("        name: \"%s\"\n", escape(t.Name)))
            desc := escape(t.Description)
            b.WriteString(fmt.Sprintf("        description: \"%s\"\n", desc))
            b.WriteString("        acceptance_criteria: []\n")
            b.WriteString(fmt.Sprintf("        estimated_hours: %d\n", t.EstimatedHours))
            b.WriteString(fmt.Sprintf("        difficulty: \"%s\"\n", t.Difficulty))
            b.WriteString("        dependencies: []\n")
            b.WriteString(fmt.Sprintf("        priority: %d\n", t.Priority))
            b.WriteString(fmt.Sprintf("        status: \"%s\"\n", t.Status))
        }
    }
    return b.String()
}

func escape(s string) string {
    s = strings.ReplaceAll(s, "\"", "\\\"")
    s = strings.ReplaceAll(s, "\n", "\\n")
    return s
}

