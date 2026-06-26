const API_URL = "/generate-skill-md";
const ZIP_API_URL = "/download-skill-zip";

let currentPlatform = "openai";
let currentSkillName = "";
let currentFiles = [];

async function generateSkillMd() {
    const platformInput = document.getElementById("platform");
    const requirementInput = document.getElementById("requirement");
    const output = document.getElementById("output");
    const generateBtn = document.getElementById("generateBtn");

    const platform = platformInput.value;
    const requirement = requirementInput.value.trim();

    if (!requirement) {
        alert("Please enter a skill requirement.");
        return;
    }

    output.innerText = "Generating complete skill package...";
    generateBtn.disabled = true;
    hideValidation();
    hidePackagePreview();

    currentPlatform = platform;
    currentSkillName = "";
    currentFiles = [];

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                platform: platform,
                requirement: requirement
            })
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error("API request failed: " + errorText);
        }

        const data = await response.json();

        console.log("API response:", data);

        currentPlatform = data.platform || platform;
        currentSkillName = data.skill_name || "generated-skill";
        currentFiles = Array.isArray(data.files) ? data.files : [];

        output.innerText = data.skill_md || "No skill markdown content returned.";

        if (data.validation) {
            showValidation(data.validation);
        } else {
            showValidation({
                is_valid: false,
                errors: ["Validation result was not returned by backend."]
            });
        }

        showPackagePreview(currentPlatform, currentSkillName, currentFiles);

    } catch (error) {
        console.error("Generate error:", error);

        output.innerText = "Something went wrong while generating the skill package. Check backend terminal and browser console.";

        showValidation({
            is_valid: false,
            errors: [error.message]
        });

    } finally {
        generateBtn.disabled = false;
    }
}

function showValidation(validation) {
    const validationBox = document.getElementById("validationBox");

    validationBox.classList.remove("hidden");
    validationBox.classList.remove("validation-success");
    validationBox.classList.remove("validation-error");

    if (validation.is_valid) {
        validationBox.classList.add("validation-success");
        validationBox.innerText = "Valid skill markdown ✅";
    } else {
        validationBox.classList.add("validation-error");

        const errors = Array.isArray(validation.errors)
            ? validation.errors
            : ["Unknown validation error."];

        const errorText = errors
            .map(function (error) {
                return "• " + error;
            })
            .join("\n");

        validationBox.innerText = "Invalid skill markdown ❌\n" + errorText;
    }
}

function hideValidation() {
    const validationBox = document.getElementById("validationBox");

    if (!validationBox) {
        return;
    }

    validationBox.classList.add("hidden");
    validationBox.classList.remove("validation-success");
    validationBox.classList.remove("validation-error");
    validationBox.innerText = "";
}

function showPackagePreview(platform, skillName, files) {
    const packagePreview = document.getElementById("packagePreview");
    const packageTree = document.getElementById("packageTree");

    if (!packagePreview || !packageTree) {
        return;
    }

    const safeSkillName = skillName || "generated-skill";

    let tree = `${safeSkillName}/  (${platform})\n`;
    tree += `├── SKILL.md\n`;

    const scripts = files.filter(file => file.path && file.path.startsWith("scripts/"));
    const references = files.filter(file => file.path && file.path.startsWith("references/"));
    const assets = files.filter(file => file.path && file.path.startsWith("assets/"));

    tree += buildFolderTree("scripts", scripts);
    tree += buildFolderTree("references", references);
    tree += buildFolderTree("assets", assets);

    packageTree.innerText = tree;
    packagePreview.classList.remove("hidden");
}

function buildFolderTree(folderName, files) {
    let text = `├── ${folderName}/\n`;

    if (!files || files.length === 0) {
        text += `│   └── .gitkeep\n`;
        return text;
    }

    files.forEach(function(file, index) {
        const fileName = file.path.replace(folderName + "/", "");
        const connector = index === files.length - 1 ? "└──" : "├──";
        text += `│   ${connector} ${fileName}\n`;
    });

    return text;
}

function hidePackagePreview() {
    const packagePreview = document.getElementById("packagePreview");
    const packageTree = document.getElementById("packageTree");

    if (!packagePreview || !packageTree) {
        return;
    }

    packagePreview.classList.add("hidden");
    packageTree.innerText = "";
}

function copyOutput() {
    const output = document.getElementById("output").innerText;

    if (!isGeneratedSkillMdAvailable(output)) {
        alert("Please generate skill markdown first.");
        return;
    }

    navigator.clipboard.writeText(output)
        .then(function () {
            alert("Skill markdown copied.");
        })
        .catch(function () {
            alert("Copy failed.");
        });
}

function downloadSkillMd() {
    const output = document.getElementById("output").innerText;

    if (!isGeneratedSkillMdAvailable(output)) {
        alert("Please generate skill markdown first.");
        return;
    }

    const blob = new Blob([output], {
        type: "text/markdown"
    });

    const url = URL.createObjectURL(blob);

    const link = document.createElement("a");
    link.href = url;
    link.download = "SKILL.md";

    document.body.appendChild(link);
    link.click();

    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

async function downloadSkillZip() {
    const output = document.getElementById("output").innerText;

    if (!isGeneratedSkillMdAvailable(output)) {
        alert("Please generate skill markdown first.");
        return;
    }

    try {
        const response = await fetch(ZIP_API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                platform: currentPlatform || "openai",
                skill_name: currentSkillName || "generated-skill",
                skill_md: output,
                files: currentFiles
            })
        });

        const contentType = response.headers.get("content-type") || "";

        if (!response.ok || contentType.includes("application/json")) {
            const errorData = await response.json();

            if (errorData.validation) {
                showValidation(errorData.validation);
            }

            alert(errorData.error || "Unable to create ZIP.");
            return;
        }

        const blob = await response.blob();

        let filename = "skill.zip";

        const contentDisposition = response.headers.get("content-disposition");

        if (contentDisposition) {
            const match = contentDisposition.match(/filename="(.+)"/);

            if (match && match[1]) {
                filename = match[1];
            }
        }

        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");
        link.href = url;
        link.download = filename;

        document.body.appendChild(link);
        link.click();

        document.body.removeChild(link);
        URL.revokeObjectURL(url);

    } catch (error) {
        console.error("ZIP download error:", error);
        alert("Something went wrong while downloading ZIP.");
    }
}

function isGeneratedSkillMdAvailable(output) {
    if (!output) {
        return false;
    }

    if (output.includes("Your generated skill markdown will appear here")) {
        return false;
    }

    if (output.includes("Generating")) {
        return false;
    }

    if (output.includes("Something went wrong")) {
        return false;
    }

    return true;
}