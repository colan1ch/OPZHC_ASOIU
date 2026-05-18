import simpy
import random
import math

def exponential(mean):
    return random.expovariate(1.0 / mean)

class GPSS_Blocks:
    def __init__(self):
        self.entry_count = {}
        self.current_count = {}
        
    def increment_entry(self, block_name):
        self.entry_count[block_name] = self.entry_count.get(block_name, 0) + 1
    
    def increment_current(self, block_name):
        self.current_count[block_name] = self.current_count.get(block_name, 0) + 1
    
    def decrement_current(self, block_name):
        self.current_count[block_name] = max(0, self.current_count.get(block_name, 0) - 1)

def customer_process(env, customer_id, barber1, barber2, stats, blocks):
    """
    1. GENERATE - создание клиента
    2. QUEUE Barber - вход в очередь
    3. QUEUE Total_time - вход в очередь
    4. TRANSFER Both,Barb1,Barb2 - выбор свободного барбера
    5. Barb1/Barb2 - SEIZE, DEPART, ADVANCE, DEPART, RELEASE
    6. Next - SAVEVALUE, TERMINATE
    """
    

    blocks.increment_entry("QUEUE_Barber")
    blocks.increment_current("QUEUE_Barber")
    queue_barber_start = env.now
    stats['barber_queue'].append(env.now)
    

    blocks.increment_entry("QUEUE_Total_time")
    blocks.increment_current("QUEUE_Total_time")
    total_time_start = env.now
    stats['total_queue'].append(env.now)
    

    blocks.increment_entry("TRANSFER")

    available_barbers = []
    if barber1.count == 0:
        available_barbers.append(('barb1', barber1))
    if barber2.count == 0:
        available_barbers.append(('barb2', barber2))
    
    if available_barbers:

        chosen = available_barbers[0]
    else:

        chosen = random.choice([('barb1', barber1), ('barb2', barber2)])
    

    chosen_name, chosen_barber = chosen
    blocks.increment_entry(f"SEIZE_{chosen_name.upper()}")
    with chosen_barber.request() as req:
        yield req
        blocks.increment_current(f"SEIZE_{chosen_name.upper()}")
        

        blocks.increment_entry("DEPART_Barber")
        queue_barber_end = env.now
        barber_queue_time = queue_barber_end - queue_barber_start
        stats['barber_queue'][-1] = barber_queue_time
        blocks.decrement_current("QUEUE_Barber")
        

        blocks.increment_entry("ADVANCE")
        if chosen_name == 'barb1':

            service_time = random.normalvariate(10, 2.5)

            service_time = max(0.1, service_time)
            stats['barber1_usage'] += 1
            stats['barber1_time'] += service_time
        else:

            service_time = random.normalvariate(13, 4)
            service_time = max(0.1, service_time)
            stats['barber2_usage'] += 1
            stats['barber2_time'] += service_time
        
        yield env.timeout(service_time)
        

        blocks.increment_entry("DEPART_Total_time")
        total_time_end = env.now
        total_system_time = total_time_end - total_time_start
        stats['total_queue'][-1] = total_system_time
        blocks.decrement_current("QUEUE_Total_time")
        

        blocks.increment_entry(f"RELEASE_{chosen_name.upper()}")
        blocks.decrement_current(f"SEIZE_{chosen_name.upper()}")
    

    blocks.increment_entry("SAVEVALUE")
    if stats['barber_queue']:
        avg_queue = sum(stats['barber_queue']) / len(stats['barber_queue'])
        stats['ave_queue'] = avg_queue
    

    blocks.increment_entry("TERMINATE")
    stats['terminated'] += 1

def customer_generator(env, barber1, barber2, stats, blocks, max_customers=105):
    """Блок 1: GENERATE (Exponential(1,0,6.5))"""
    customers_created = 0
    while customers_created < max_customers:

        interarrival_time = exponential(6.5)
        yield env.timeout(interarrival_time)
        
        blocks.increment_entry("GENERATE")
        customers_created += 1
        stats['generated'] = customers_created
        

        env.process(customer_process(env, customers_created, barber1, barber2, stats, blocks))

def run_simulation(runtime=615.122, max_customers=105):

    env = simpy.Environment()
    

    barber1 = simpy.Resource(env, capacity=1)
    barber2 = simpy.Resource(env, capacity=1)
    

    stats = {
        'generated': 0,
        'terminated': 0,
        'barber_queue': [],      # Время в очереди Barber
        'total_queue': [],       # Общее время в системе
        'barber1_usage': 0,
        'barber2_usage': 0,
        'barber1_time': 0,
        'barber2_time': 0,
        'ave_queue': 0
    }
    

    blocks = GPSS_Blocks()
    

    env.process(customer_generator(env, barber1, barber2, stats, blocks, max_customers))
    

    env.run(until=runtime)
    

    print_report(env, stats, blocks, runtime, max_customers)

def print_report(env, stats, blocks, runtime, max_customers):
    print("\n" + " " * 18 + "GPSS World Simulation Report - Sampque.1.1 (Python/SimPy)")
    print(" " * 16 + "=" * 60)
    print(f"\n           START TIME           END TIME  BLOCKS  FACILITIES  STORAGES")
    print(f"            {0.000:10.3f}          {env.now:10.3f}    17        2          0\n")
    

    print("\n LABEL              LOC  BLOCK TYPE     ENTRY COUNT CURRENT COUNT RETRY")
    blocks_list = [
        ("", 1, "GENERATE", stats['generated'], 0),
        ("", 2, "QUEUE", blocks.entry_count.get("QUEUE_Barber", 0), 
         blocks.current_count.get("QUEUE_Barber", 0)),
        ("", 3, "QUEUE", blocks.entry_count.get("QUEUE_Total_time", 0),
         blocks.current_count.get("QUEUE_Total_time", 0)),
        ("", 4, "TRANSFER", blocks.entry_count.get("TRANSFER", 0), 0),
        ("BARB1", 5, "SEIZE", blocks.entry_count.get("SEIZE_BARB1", 0),
         blocks.current_count.get("SEIZE_BARB1", 0)),
        ("", 6, "DEPART", blocks.entry_count.get("DEPART_Barber", 0), 0),
        ("", 7, "ADVANCE", blocks.entry_count.get("ADVANCE", 0) // 2, 0),  # Примерно
        ("", 8, "DEPART", blocks.entry_count.get("DEPART_Total_time", 0), 0),
        ("", 9, "RELEASE", blocks.entry_count.get("RELEASE_BARB1", 0), 0),
        ("", 10, "TRANSFER", blocks.entry_count.get("TRANSFER", 0) // 2, 0),
        ("BARB2", 11, "SEIZE", blocks.entry_count.get("SEIZE_BARB2", 0),
         blocks.current_count.get("SEIZE_BARB2", 0)),
        ("", 12, "DEPART", blocks.entry_count.get("DEPART_Barber", 0), 0),
        ("", 13, "ADVANCE", blocks.entry_count.get("ADVANCE", 0) // 2, 0),
        ("", 14, "DEPART", blocks.entry_count.get("DEPART_Total_time", 0), 0),
        ("", 15, "RELEASE", blocks.entry_count.get("RELEASE_BARB2", 0), 0),
        ("NEXT", 16, "SAVEVALUE", blocks.entry_count.get("SAVEVALUE", 0), 0),
        ("FINIS", 17, "TERMINATE", stats['terminated'], 0)
    ]
    
    for label, loc, btype, entry, current in blocks_list:
        print(f" {label:6} {loc:3}   {btype:10} {entry:12} {current:12} 0")
    

    print("\n\nFACILITY         ENTRIES  UTIL.   AVE. TIME AVAIL. OWNER PEND INTER RETRY DELAY")
    if stats['barber1_usage'] > 0:
        util1 = stats['barber1_time'] / env.now
        avg_time1 = stats['barber1_time'] / stats['barber1_usage']
        print(f" BARBER1            {stats['barber1_usage']:3}    {util1:.3f}     {avg_time1:8.3f}  1       0    0    0     0      0")
    if stats['barber2_usage'] > 0:
        util2 = stats['barber2_time'] / env.now
        avg_time2 = stats['barber2_time'] / stats['barber2_usage']
        print(f" BARBER2            {stats['barber2_usage']:3}    {util2:.3f}     {avg_time2:8.3f}  1       0    0    0     0      0")
    

    print("\n\nQUEUE              MAX CONT. ENTRY ENTRY(0) AVE.CONT. AVE.TIME   AVE.(-0) RETRY")
    
    if stats['barber_queue']:
        max_barber = max(stats['barber_queue']) if stats['barber_queue'] else 0
        entry_barber = len(stats['barber_queue'])
        entry0_barber = sum(1 for t in stats['barber_queue'] if t < 0.001)
        avg_cont_barber = sum(stats['barber_queue']) / env.now if env.now > 0 else 0
        avg_time_barber = sum(stats['barber_queue']) / entry_barber if entry_barber > 0 else 0
        avg_time_no0 = sum(t for t in stats['barber_queue'] if t >= 0.001) / max(1, entry_barber - entry0_barber)
        print(f" BARBER             {max_barber:3.0f}    {entry_barber:5}     {entry0_barber:3}     {avg_cont_barber:7.3f}    {avg_time_barber:7.3f}    {avg_time_no0:8.3f}   0")
    
    if stats['total_queue']:
        max_total = max(stats['total_queue']) if stats['total_queue'] else 0
        entry_total = len(stats['total_queue'])
        entry0_total = sum(1 for t in stats['total_queue'] if t < 0.001)
        avg_cont_total = sum(stats['total_queue']) / env.now if env.now > 0 else 0
        avg_time_total = sum(stats['total_queue']) / entry_total if entry_total > 0 else 0
        print(f" TOTAL_TIME         {max_total:3.0f}    {entry_total:5}     {entry0_total:3}     {avg_cont_total:7.3f}    {avg_time_total:7.3f}    {avg_time_total:8.3f}   0")
    

    print("\n\nSAVEVALUE               RETRY       VALUE")
    print(f" AVE_QUEUE                0        {stats['ave_queue']:.3f}")
    

    print("\n\nCEC XN   PRI          M1      ASSEM  CURRENT  NEXT  PARAMETER    VALUE")

    print("   -    -            -        -      -       -        -          -")
    

    print("\n\nFEC XN   PRI         BDT      ASSEM  CURRENT  NEXT  PARAMETER    VALUE")
    print(f"   1    0        {env.now+100:.3f}      1       0      1")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    random.seed(42)  # Для воспроизводимости
    run_simulation(runtime=615.122, max_customers=105)
