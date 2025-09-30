package com.example;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import org.crac.Core;
import org.crac.Resource;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;
import java.util.List;
import java.util.ArrayList;

public class SnapStartLambdaHandler implements RequestHandler<Map<String, Object>, Map<String, Object>>, Resource {

    private static List<String> preloadedData;
    private static boolean isInitialized = false;

    public SnapStartLambdaHandler() {
        System.out.println("SnapStart Handler constructor called");
        // Register this class as a CRaC resource
        Core.getGlobalContext().register(this);
    }

    // Static initialization
    static {
        System.out.println("SnapStart: Static initialization starting...");
        preloadData();
        System.out.println("SnapStart: Static initialization completed");
    }

    // Pre-load data during static initialization
    private static void preloadData() {
        preloadedData = new ArrayList<>();
        for (int i = 0; i < 1000; i++) {
            preloadedData.add("PreloadedItem_" + i + "_" + Math.random());
        }
    }

    @Override
    public void beforeCheckpoint(org.crac.Context<? extends Resource> context) throws Exception {
        System.out.println("SnapStart: beforeCheckpoint hook called - preparing for snapshot");

        // Class priming - ensure critical classes are loaded
        primeCriticalClasses();

        // Invoke priming - warm up code paths
        performWarmupInvocations();

        // Mark as initialized
        isInitialized = true;

        System.out.println("SnapStart: beforeCheckpoint completed successfully");
    }

    @Override
    public void afterRestore(org.crac.Context<? extends Resource> context) throws Exception {
        System.out.println("SnapStart: afterRestore hook called - Lambda restored from snapshot");

        // Re-establish any connections or state that can't be checkpointed
        reinitializeConnections();

        System.out.println("SnapStart: afterRestore completed successfully");
    }

    private void primeCriticalClasses() {
        // Load and initialize commonly used classes
        try {
            Class.forName("java.util.HashMap");
            Class.forName("java.util.ArrayList");
            Class.forName("java.lang.StringBuilder");
            Class.forName("com.fasterxml.jackson.databind.ObjectMapper");

            System.out.println("Critical classes primed successfully");
        } catch (ClassNotFoundException e) {
            System.err.println("Error priming classes: " + e.getMessage());
        }
    }

    private void performWarmupInvocations() {
        // Execute common code paths to warm up JIT compilation
        Map<String, Object> dummyEvent = new HashMap<>();
        dummyEvent.put("warmup", true);

        // Perform a few warmup calculations
        for (int i = 0; i < 10; i++) {
            double result = Math.sqrt(i * 100) + Math.random();
            String formatted = String.format("Warmup calculation %d: %.2f", i, result);
            // Use the formatted string to ensure string formatting code path is warmed up
            if (i == 0) {
                System.out.println("Sample warmup output: " + formatted);
            }
        }

        System.out.println("Warmup invocations completed");
    }

    private void reinitializeConnections() {
        // In a real application, you would re-establish database connections,
        // HTTP clients, or other stateful connections here
        System.out.println("Connections reinitialized after restore");
    }

    @Override
    public Map<String, Object> handleRequest(Map<String, Object> event, Context context) {
        long startTime = System.currentTimeMillis();

        System.out.println("SnapStart Handler processing request: " + context.getAwsRequestId());
        System.out.println("Is initialized from snapshot: " + isInitialized);

        // Simulate business logic using preloaded data
        String result = performOptimizedBusinessLogic();

        long processingTime = System.currentTimeMillis() - startTime;

        // Create response
        Map<String, Object> response = new HashMap<>();
        response.put("statusCode", 200);
        response.put("message", "SnapStart Lambda processing completed");
        response.put("result", result);
        response.put("requestId", context.getAwsRequestId());
        response.put("processingTimeMs", processingTime);
        response.put("remainingTimeMs", context.getRemainingTimeInMillis());
        response.put("memoryLimitMB", context.getMemoryLimitInMB());
        response.put("timestamp", System.currentTimeMillis());
        response.put("snapStartInitialized", isInitialized);
        response.put("preloadedDataSize", preloadedData != null ? preloadedData.size() : 0);

        return response;
    }

    private String performOptimizedBusinessLogic() {
        // Use preloaded data for faster processing
        int randomIndex = ThreadLocalRandom.current().nextInt(0, preloadedData.size());
        String preloadedItem = preloadedData.get(randomIndex);

        // Perform some computation
        int randomValue = ThreadLocalRandom.current().nextInt(1000, 10000);
        double calculation = Math.pow(randomValue, 2) + Math.sqrt(randomValue);

        return String.format("SnapStart optimized result: %.2f, using: %s", calculation, preloadedItem);
    }
}
