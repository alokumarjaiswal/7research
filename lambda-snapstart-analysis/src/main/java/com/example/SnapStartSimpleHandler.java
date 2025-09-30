package com.example;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ThreadLocalRandom;
import java.util.List;
import java.util.ArrayList;

public class SnapStartSimpleHandler implements RequestHandler<Map<String, Object>, Map<String, Object>> {

    private static List<String> preloadedData;
    private static boolean isInitialized = false;

    // Static initialization - this will be checkpointed by SnapStart
    static {
        System.out.println("SnapStart Simple: Static initialization starting...");
        long startTime = System.currentTimeMillis();

        // Simulate heavy initialization
        preloadData();
        performHeavyComputation();

        long initTime = System.currentTimeMillis() - startTime;
        System.out.println("SnapStart Simple: Static initialization completed in " + initTime + "ms");
        isInitialized = true;
    }

    private static void preloadData() {
        preloadedData = new ArrayList<>();
        for (int i = 0; i < 10000; i++) {
            preloadedData.add("PreloadedItem_" + i + "_" + Math.random());
        }
    }

    private static void performHeavyComputation() {
        // Simulate expensive initialization
        double result = 0;
        for (int i = 0; i < 2000000; i++) {
            result += Math.sqrt(i) * Math.random();
        }
        System.out.println("Heavy computation result: " + result);
    }

    @Override
    public Map<String, Object> handleRequest(Map<String, Object> event, Context context) {
        long startTime = System.currentTimeMillis();

        System.out.println("SnapStart Simple Handler processing request: " + context.getAwsRequestId());
        System.out.println("Pre-initialization completed: " + isInitialized);

        String result = performBusinessLogic();
        long processingTime = System.currentTimeMillis() - startTime;

        Map<String, Object> response = new HashMap<>();
        response.put("statusCode", 200);
        response.put("message", "SnapStart Simple Lambda processing completed");
        response.put("result", result);
        response.put("requestId", context.getAwsRequestId());
        response.put("processingTimeMs", processingTime);
        response.put("remainingTimeMs", context.getRemainingTimeInMillis());
        response.put("memoryLimitMB", context.getMemoryLimitInMB());
        response.put("timestamp", System.currentTimeMillis());
        response.put("preInitialized", isInitialized);
        response.put("preloadedDataSize", preloadedData != null ? preloadedData.size() : 0);

        return response;
    }

    private String performBusinessLogic() {
        int randomIndex = ThreadLocalRandom.current().nextInt(0, preloadedData.size());
        String preloadedItem = preloadedData.get(randomIndex);

        int randomValue = ThreadLocalRandom.current().nextInt(1000, 10000);
        double calculation = Math.pow(randomValue, 2) + Math.sqrt(randomValue);

        return String.format("SnapStart result: %.2f, using: %s", calculation, preloadedItem);
    }
}
